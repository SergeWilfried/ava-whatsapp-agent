import mongoose from 'mongoose';
import { Business } from '../models/Business';
import logger from '../utils/logger';
import * as dotenv from 'dotenv';

// Load environment variables
dotenv.config();

/**
 * Script to extract WhatsApp credentials from MongoDB
 *
 * Usage:
 *   npx ts-node scripts/extractWhatsAppCredentials.ts
 *   npx ts-node scripts/extractWhatsAppCredentials.ts <subDomain>
 */

interface WhatsAppCredentials {
  businessName: string;
  subDomain: string;
  wabaId: string | undefined;
  phoneNumberIds: string[];
  accessToken: string | null;
  refreshToken: string | null;
  tokenExpiresAt: Date | undefined;
  whatsappEnabled: boolean | undefined;
}

async function extractCredentials(subDomain?: string): Promise<void> {
  try {
    // Connect to MongoDB
    const mongoUri = process.env.MONGODB_URI;
    if (!mongoUri) {
      throw new Error('MONGODB_URI not found in environment variables');
    }

    logger.info('Connecting to MongoDB...');
    await mongoose.connect(mongoUri);
    logger.info('Connected to MongoDB successfully');

    // Build query
    const query: any = { whatsappEnabled: true };
    if (subDomain) {
      query.subDomain = subDomain;
    }

    // Find businesses with WhatsApp enabled
    const businesses = await Business.find(query).select(
      'name subDomain wabaId whatsappPhoneNumberIds whatsappAccessToken whatsappRefreshToken whatsappTokenExpiresAt whatsappEnabled'
    );

    if (businesses.length === 0) {
      if (subDomain) {
        logger.warn(`No business found with subdomain: ${subDomain} and WhatsApp enabled`);
      } else {
        logger.warn('No businesses found with WhatsApp enabled');
      }
      return;
    }

    logger.info(`Found ${businesses.length} business(es) with WhatsApp enabled`);
    console.log('\n' + '='.repeat(80));
    console.log('WhatsApp Credentials Extraction');
    console.log('='.repeat(80) + '\n');

    const credentials: WhatsAppCredentials[] = [];

    for (const business of businesses) {
      const decryptedAccessToken = business.getDecryptedWhatsAppAccessToken();
      const decryptedRefreshToken = business.getDecryptedWhatsAppRefreshToken();

      const cred: WhatsAppCredentials = {
        businessName: business.name,
        subDomain: business.subDomain,
        wabaId: business.wabaId,
        phoneNumberIds: business.whatsappPhoneNumberIds || [],
        accessToken: decryptedAccessToken,
        refreshToken: decryptedRefreshToken,
        tokenExpiresAt: business.whatsappTokenExpiresAt,
        whatsappEnabled: business.whatsappEnabled
      };

      credentials.push(cred);

      // Display credentials
      console.log(`Business: ${cred.businessName}`);
      console.log(`Subdomain: ${cred.subDomain}`);
      console.log(`-`.repeat(80));
      console.log(`WABA ID: ${cred.wabaId || 'Not set'}`);
      console.log(`Phone Number IDs: ${cred.phoneNumberIds.length > 0 ? cred.phoneNumberIds.join(', ') : 'None'}`);
      console.log(`Access Token: ${cred.accessToken ? `${cred.accessToken.substring(0, 20)}...` : 'Not available'}`);
      console.log(`Refresh Token: ${cred.refreshToken ? `${cred.refreshToken.substring(0, 20)}...` : 'Not available'}`);
      console.log(`Token Expires At: ${cred.tokenExpiresAt ? cred.tokenExpiresAt.toISOString() : 'Not set'}`);
      console.log(`WhatsApp Enabled: ${cred.whatsappEnabled}`);
      console.log('\n' + '-'.repeat(80) + '\n');

      // Display full tokens (use with caution)
      if (cred.accessToken || cred.phoneNumberIds.length > 0) {
        console.log('FULL CREDENTIALS (Keep secure!):');
        console.log('--------------------------------');
        if (cred.phoneNumberIds.length > 0) {
          console.log(`WHATSAPP_PHONE_NUMBER_ID=${cred.phoneNumberIds[0]}`);
        }
        if (cred.accessToken) {
          console.log(`WHATSAPP_ACCESS_TOKEN=${cred.accessToken}`);
        }
        if (cred.wabaId) {
          console.log(`WABA_ID=${cred.wabaId}`);
        }
        console.log('\n' + '='.repeat(80) + '\n');
      }
    }

    // Summary
    console.log('\nSUMMARY:');
    console.log(`Total businesses with WhatsApp: ${credentials.length}`);
    console.log(`Businesses with access tokens: ${credentials.filter(c => c.accessToken).length}`);
    console.log(`Businesses with phone number IDs: ${credentials.filter(c => c.phoneNumberIds.length > 0).length}`);

  } catch (error) {
    logger.error('Error extracting credentials:', error);
    throw error;
  } finally {
    // Disconnect from MongoDB
    await mongoose.disconnect();
    logger.info('Disconnected from MongoDB');
  }
}

// Main execution
const main = async () => {
  try {
    const subDomain = process.argv[2]; // Optional subdomain argument
    await extractCredentials(subDomain);
    process.exit(0);
  } catch (error) {
    logger.error('Script failed:', error);
    process.exit(1);
  }
};

main();
