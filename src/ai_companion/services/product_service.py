"""
Product Service - Manages products, catalog, and Meta integration
"""
import logging
import os
from typing import Optional, List, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import httpx

from ai_companion.models.schemas import Product, Category, Presentation, Modifier

logger = logging.getLogger(__name__)


class ProductService:
    """Service for managing products and Meta Catalog integration"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.products_collection = db.products
        self.categories_collection = db.categories
        self.presentations_collection = db.presentations
        self.modifiers_collection = db.modifiers
        self.businesses_collection = db.businesses

    async def get_products_by_category(
        self,
        sub_domain: str,
        category_id: Optional[str] = None,
        local_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Product]:
        """
        Get products for a business, optionally filtered by category.

        Args:
            sub_domain: Business subdomain
            category_id: Optional category ID to filter
            local_id: Optional location ID
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of Product objects
        """
        try:
            query = {
                "subDomain": sub_domain,
                "isActive": True,
                "isAvailable": True
            }

            if local_id:
                query["localId"] = local_id

            if category_id:
                query["categoryId"] = category_id

            cursor = self.products_collection.find(query).sort("sortOrder", 1).skip(offset).limit(limit)

            products = []
            async for doc in cursor:
                try:
                    # Convert _id to string
                    doc["_id"] = str(doc["_id"])
                    product = Product(**doc)
                    products.append(product)
                except Exception as e:
                    logger.error(f"Failed to parse product: {e}", extra={"doc": doc})
                    continue

            logger.info(f"Retrieved {len(products)} products for {sub_domain}")
            return products

        except Exception as e:
            logger.error(f"Failed to get products: {e}", exc_info=True)
            return []

    async def get_product_by_id(
        self,
        product_id: str,
        sub_domain: str
    ) -> Optional[Product]:
        """
        Get product by rId.

        Args:
            product_id: Product rId
            sub_domain: Business subdomain

        Returns:
            Product object or None
        """
        try:
            doc = await self.products_collection.find_one({
                "rId": product_id,
                "subDomain": sub_domain,
                "isActive": True
            })

            if not doc:
                logger.warning(f"Product not found: {product_id}")
                return None

            doc["_id"] = str(doc["_id"])
            return Product(**doc)

        except Exception as e:
            logger.error(f"Failed to get product {product_id}: {e}", exc_info=True)
            return None

    async def get_presentations_for_product(
        self,
        product_id: str,
        sub_domain: str
    ) -> List[Presentation]:
        """
        Get all presentations for a product.

        Args:
            product_id: Product rId
            sub_domain: Business subdomain

        Returns:
            List of Presentation objects
        """
        try:
            # First get product to get presentation IDs
            product = await self.get_product_by_id(product_id, sub_domain)
            if not product or not product.presentations:
                return []

            cursor = self.presentations_collection.find({
                "rId": {"$in": product.presentations},
                "isActive": True
            })

            presentations = []
            async for doc in cursor:
                try:
                    doc["_id"] = str(doc["_id"])
                    presentation = Presentation(**doc)
                    presentations.append(presentation)
                except Exception as e:
                    logger.error(f"Failed to parse presentation: {e}")
                    continue

            return presentations

        except Exception as e:
            logger.error(f"Failed to get presentations for {product_id}: {e}", exc_info=True)
            return []

    async def get_modifiers_for_product(
        self,
        product_id: str,
        sub_domain: str
    ) -> List[Modifier]:
        """
        Get all modifiers for a product.

        Args:
            product_id: Product rId
            sub_domain: Business subdomain

        Returns:
            List of Modifier objects
        """
        try:
            product = await self.get_product_by_id(product_id, sub_domain)
            if not product or not product.modifiers:
                return []

            # Get full modifier details from modifiers collection
            modifier_ids = [m.id for m in product.modifiers]
            cursor = self.modifiers_collection.find({
                "rId": {"$in": modifier_ids}
            })

            modifiers = []
            async for doc in cursor:
                try:
                    doc["_id"] = str(doc["_id"])
                    modifier = Modifier(**doc)
                    modifiers.append(modifier)
                except Exception as e:
                    logger.error(f"Failed to parse modifier: {e}")
                    continue

            return modifiers

        except Exception as e:
            logger.error(f"Failed to get modifiers for {product_id}: {e}", exc_info=True)
            return []

    async def get_categories(
        self,
        sub_domain: str,
        local_id: Optional[str] = None
    ) -> List[Category]:
        """
        Get all categories for a business.

        Args:
            sub_domain: Business subdomain
            local_id: Optional location ID

        Returns:
            List of Category objects
        """
        try:
            query = {
                "subDomain": sub_domain,
                "isActive": True
            }

            if local_id:
                query["localId"] = local_id

            cursor = self.categories_collection.find(query).sort("sortOrder", 1)

            categories = []
            async for doc in cursor:
                try:
                    doc["_id"] = str(doc["_id"])
                    category = Category(**doc)
                    categories.append(category)
                except Exception as e:
                    logger.error(f"Failed to parse category: {e}")
                    continue

            return categories

        except Exception as e:
            logger.error(f"Failed to get categories: {e}", exc_info=True)
            return []

    async def sync_product_to_meta_catalog(
        self,
        product: Product,
        business_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Sync a single product to Meta Commerce Manager catalog.

        Args:
            product: Product object
            business_data: Business credentials and config

        Returns:
            Dict with success status and catalogId
        """
        try:
            # Get business Meta credentials
            access_token = business_data.get("decryptedAccessToken")
            fb_business_id = business_data.get("fbBusinessId")
            fb_catalog_mapping = business_data.get("fbCatalogMapping", {})

            if not access_token or not fb_business_id:
                logger.warning(f"Missing Meta credentials for {product.sub_domain}")
                return {"success": False, "error": "Missing Meta credentials"}

            # Get or create catalog ID for this product's category
            catalog_id = fb_catalog_mapping.get(product.category_id)

            if not catalog_id:
                # Create catalog for this category
                catalog_result = await self._create_category_catalog(
                    business_id=fb_business_id,
                    category_id=product.category_id,
                    category_name=product.category,
                    access_token=access_token
                )

                if not catalog_result.get("success"):
                    return catalog_result

                catalog_id = catalog_result["catalogId"]

                # Store catalog mapping in business
                await self.businesses_collection.update_one(
                    {"subDomain": product.sub_domain},
                    {"$set": {f"fbCatalogMapping.{product.category_id}": catalog_id}}
                )

            # Sync product to catalog
            result = await self._sync_product_to_catalog(
                catalog_id=catalog_id,
                product=product,
                access_token=access_token
            )

            return {
                "success": result.get("success", False),
                "catalogId": catalog_id,
                "action": result.get("action", "unknown")
            }

        except Exception as e:
            logger.error(f"Failed to sync product to Meta catalog: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def _create_category_catalog(
        self,
        business_id: str,
        category_id: str,
        category_name: str,
        access_token: str
    ) -> Dict[str, Any]:
        """Create a Meta catalog for a product category"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"https://graph.facebook.com/v21.0/{business_id}/owned_product_catalogs",
                    headers={"Authorization": f"Bearer {access_token}"},
                    json={
                        "name": f"{category_name} Catalog",
                        "vertical": "ecommerce"
                    }
                )

                response.raise_for_status()
                data = response.json()

                catalog_id = data.get("id")
                logger.info(f"Created Meta catalog for category {category_id}: {catalog_id}")

                return {
                    "success": True,
                    "catalogId": catalog_id
                }

        except httpx.HTTPStatusError as e:
            error_data = e.response.json() if e.response else {}
            logger.error(f"Meta API error creating catalog: {error_data}")
            return {
                "success": False,
                "error": error_data.get("error", {}).get("message", str(e))
            }
        except Exception as e:
            logger.error(f"Failed to create Meta catalog: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def _sync_product_to_catalog(
        self,
        catalog_id: str,
        product: Product,
        access_token: str
    ) -> Dict[str, Any]:
        """Sync product to Meta catalog"""
        try:
            # Prepare product data for Meta API
            meta_product = {
                "retailer_id": product.r_id,  # Your internal ID
                "name": product.name,
                "description": product.description or "",
                "price": int(product.base_price * 100),  # Convert to cents
                "currency": "PEN",  # TODO: Get from business settings
                "availability": "in stock" if not product.is_out_of_stock else "out of stock",
                "condition": "new",
                "url": f"https://{product.sub_domain}.lemenu.pe/products/{product.r_id}"
            }

            # Add image if available
            if product.image_url:
                meta_product["image_url"] = product.image_url

            # Check if product already exists in catalog
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Try to update existing product first
                try:
                    update_response = await client.post(
                        f"https://graph.facebook.com/v21.0/{catalog_id}/products",
                        headers={"Authorization": f"Bearer {access_token}"},
                        json={
                            "retailer_id": product.r_id,
                            "data": meta_product
                        }
                    )

                    update_response.raise_for_status()
                    logger.info(f"Updated product in Meta catalog: {product.r_id}")

                    return {
                        "success": True,
                        "action": "updated"
                    }

                except httpx.HTTPStatusError as e:
                    # Product doesn't exist, create it
                    if e.response.status_code == 404 or "does not exist" in str(e.response.text):
                        create_response = await client.post(
                            f"https://graph.facebook.com/v21.0/{catalog_id}/products",
                            headers={"Authorization": f"Bearer {access_token}"},
                            json=meta_product
                        )

                        create_response.raise_for_status()
                        logger.info(f"Created product in Meta catalog: {product.r_id}")

                        return {
                            "success": True,
                            "action": "created"
                        }
                    else:
                        raise

        except httpx.HTTPStatusError as e:
            error_data = e.response.json() if e.response else {}
            logger.error(f"Meta API error syncing product: {error_data}")
            return {
                "success": False,
                "error": error_data.get("error", {}).get("message", str(e))
            }
        except Exception as e:
            logger.error(f"Failed to sync product to catalog: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def remove_product_from_catalog(
        self,
        product_id: str,
        sub_domain: str
    ) -> Dict[str, Any]:
        """
        Remove product from Meta catalog.

        Args:
            product_id: Product rId
            sub_domain: Business subdomain

        Returns:
            Dict with success status
        """
        try:
            # Get business credentials
            business = await self.businesses_collection.find_one({
                "subDomain": sub_domain
            })

            if not business:
                return {"success": False, "error": "Business not found"}

            access_token = business.get("decryptedAccessToken")
            fb_catalog_mapping = business.get("fbCatalogMapping", {})

            if not access_token:
                return {"success": False, "error": "No access token"}

            # Get product to find its catalog
            product = await self.get_product_by_id(product_id, sub_domain)
            if not product:
                return {"success": False, "error": "Product not found"}

            catalog_id = fb_catalog_mapping.get(product.category_id)
            if not catalog_id:
                logger.warning(f"No catalog found for product {product_id}")
                return {"success": True, "action": "skipped"}

            # Delete from Meta catalog
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(
                    f"https://graph.facebook.com/v21.0/{catalog_id}/products",
                    headers={"Authorization": f"Bearer {access_token}"},
                    json={"retailer_id": product_id}
                )

                response.raise_for_status()
                logger.info(f"Removed product from Meta catalog: {product_id}")

                return {
                    "success": True,
                    "action": "deleted"
                }

        except httpx.HTTPStatusError as e:
            error_data = e.response.json() if e.response else {}
            logger.error(f"Meta API error removing product: {error_data}")
            return {
                "success": False,
                "error": error_data.get("error", {}).get("message", str(e))
            }
        except Exception as e:
            logger.error(f"Failed to remove product from catalog: {e}", exc_info=True)
            return {"success": False, "error": str(e)}


# Global instance
_product_service: Optional[ProductService] = None


async def get_product_service(db: AsyncIOMotorDatabase) -> ProductService:
    """Get or create global ProductService instance"""
    global _product_service

    if _product_service is None:
        _product_service = ProductService(db)

    return _product_service
