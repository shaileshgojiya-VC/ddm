"""
Microsoft Graph API client utility for email collection.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from azure.identity.aio import ClientSecretCredential

from config.env_config import settings

logger = logging.getLogger(__name__)


class MicrosoftGraphClient:
    """
    Microsoft Graph API client for email operations.

    Handles authentication, token management, and API calls for:
    - Client credentials authentication
    - Delta sync queries
    - Webhook subscriptions
    - Message retrieval
    - Attachment retrieval
    """

    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
    ):
        """
        Initialize Microsoft Graph client.

        Args:
            tenant_id: Azure tenant ID
            client_id: Azure client ID
            client_secret: Azure client secret
        """
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self._token_expires_at: Optional[datetime] = None

    def _is_token_expiring(self) -> bool:
        """
        Check if token is expiring soon (within 5 minutes).

        Returns:
            True if token is expiring, False otherwise
        """
        if self._token_expires_at is None:
            return True
        return datetime.utcnow() + timedelta(minutes=5) >= self._token_expires_at

    async def validate_credentials(self) -> bool:
        """
        Validate client credentials by attempting to get a token.

        Returns:
            True if credentials are valid, False otherwise
        """
        try:
            logger.info("STEP 1: Validating Microsoft Graph credentials")
            graph_url = "https://graph.microsoft.com/v1.0/users?$top=1"
            async with httpx.AsyncClient() as http_client:
                headers = await self._get_headers()
                response = await http_client.get(graph_url, headers=headers)
                response.raise_for_status()
            logger.info("STEP 2: Credentials validated successfully")
            return True
        except Exception as exc:
            logger.error(f"Credential validation failed: {exc}", exc_info=True)
            return False

    async def get_user_messages_delta(
        self, user_email: str, delta_link: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get messages using delta query with pagination support.

        Fetches all pages until we get the final delta link.

        Args:
            user_email: User email address
            delta_link: Previous delta link for incremental sync

        Returns:
            Dictionary containing all messages and final delta link
        """
        try:
            logger.info(f"STEP 1: Starting delta query for {user_email}")

            all_messages = []
            next_link = None
            final_delta_link = None
            page_count = 0

            if delta_link:
                logger.info("STEP 2: Using existing delta link for incremental sync")
                next_link = delta_link
            else:
                logger.info("STEP 2: Starting initial delta query")
                next_link = f"https://graph.microsoft.com/v1.0/users/{user_email}/mailFolders/inbox/messages/delta"

            async with httpx.AsyncClient() as http_client:
                headers = await self._get_headers()

                # Follow pagination until we get the final delta link
                while next_link:
                    page_count += 1
                    logger.info(
                        f"STEP 3: Fetching page {page_count} from {next_link[:100]}..."
                    )

                    response = await http_client.get(next_link, headers=headers)
                    response.raise_for_status()
                    data = response.json()

                    # Collect messages from this page
                    page_messages = data.get("value", [])
                    all_messages.extend(page_messages)
                    logger.info(
                        f"STEP 4: Page {page_count} returned {len(page_messages)} messages (total so far: {len(all_messages)})"
                    )

                    # Check for next page or final delta link
                    next_link = data.get("@odata.nextLink")
                    final_delta_link = data.get("@odata.deltaLink")

                    # If we have a delta link, we're done (this is the final page)
                    if final_delta_link:
                        logger.info(
                            f"STEP 5: Received final delta link, pagination complete"
                        )
                        break

                    # If no next link and no delta link, we're done
                    if not next_link:
                        logger.info(f"STEP 5: No more pages available")
                        break

            logger.info(
                f"STEP 6: Retrieved {len(all_messages)} total messages across {page_count} pages"
            )

            return {
                "value": all_messages,
                "@odata.deltaLink": final_delta_link,
            }
        except Exception as exc:
            logger.error(f"Delta query failed: {exc}", exc_info=True)
            raise

    async def get_user_messages_delta_filtered(
        self,
        user_email: str,
        filter_emails: Optional[List[str]] = None,
        delta_link: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get messages using delta query with optional email filtering.

        Fetches all messages first, then filters to only include those
        that have conversations with the specified filter emails.

        Args:
            user_email: User email address
            filter_emails: List of email addresses to filter by (optional)
            delta_link: Previous delta link for incremental sync

        Returns:
            Dictionary containing filtered messages and final delta link
        """
        try:
            logger.info(f"STEP 1: Starting filtered delta query for {user_email}")

            # First, get all messages using delta query
            delta_result = await self.get_user_messages_delta(
                user_email=user_email, delta_link=delta_link
            )

            all_messages = delta_result.get("value", [])
            final_delta_link = delta_result.get("@odata.deltaLink")

            # If no filter emails provided, return all messages
            if not filter_emails:
                logger.info("STEP 2: No filter emails provided, returning all messages")
                return {
                    "value": all_messages,
                    "@odata.deltaLink": final_delta_link,
                }

            # Filter messages that have conversations with filter emails
            logger.info(
                f"STEP 2: Filtering messages for {len(filter_emails)} target emails"
            )
            filtered_messages = []
            filter_emails_set = set(email.lower() for email in filter_emails)

            for message in all_messages:
                # Check sender
                sender = message.get("sender", {})
                sender_email = (
                    sender.get("emailAddress", {}).get("address", "").lower()
                    if sender
                    else ""
                )

                # Check receivers
                to_recipients = message.get("toRecipients", [])
                receiver_emails = [
                    recipient.get("emailAddress", {}).get("address", "").lower()
                    for recipient in to_recipients
                ]

                # Check CC recipients
                cc_recipients = message.get("ccRecipients", [])
                cc_emails = [
                    recipient.get("emailAddress", {}).get("address", "").lower()
                    for recipient in cc_recipients
                ]

                # Check if any filter email is in sender, receivers, or CC
                all_participants = (
                    {sender_email} | set(receiver_emails) | set(cc_emails)
                )
                all_participants.discard("")  # Remove empty strings

                if filter_emails_set.intersection(all_participants):
                    filtered_messages.append(message)

            logger.info(
                f"STEP 3: Filtered {len(filtered_messages)} messages from {len(all_messages)} total messages"
            )

            return {
                "value": filtered_messages,
                "@odata.deltaLink": final_delta_link,
            }

        except Exception as exc:
            logger.error(f"Filtered delta query failed: {exc}", exc_info=True)
            raise

    async def _get_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for direct HTTP calls.

        Returns:
            Dictionary of headers
        """
        credential = ClientSecretCredential(
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            client_secret=self.client_secret,
        )
        token = await credential.get_token("https://graph.microsoft.com/.default")
        return {
            "Authorization": f"Bearer {token.token}",
            "Content-Type": "application/json",
        }

    async def get_message_attachments(
        self, user_email: str, message_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get attachments for a message.

        Args:
            user_email: User email address
            message_id: Message ID

        Returns:
            List of attachment dictionaries
        """
        try:
            logger.info(f"STEP 1: Fetching attachments for message {message_id}")
            graph_url = f"https://graph.microsoft.com/v1.0/users/{user_email}/messages/{message_id}/attachments"

            async with httpx.AsyncClient() as http_client:
                headers = await self._get_headers()
                response = await http_client.get(graph_url, headers=headers)
                response.raise_for_status()
                data = response.json()

            result = []
            if data.get("value"):
                for attachment in data["value"]:
                    result.append(
                        {
                            "id": attachment.get("id"),
                            "name": attachment.get("name"),
                            "contentType": attachment.get("contentType"),
                            "size": attachment.get("size"),
                        }
                    )

            logger.info(f"STEP 2: Found {len(result)} attachments")
            return result
        except Exception as exc:
            logger.error(f"Failed to fetch attachments: {exc}", exc_info=True)
            return []

    async def _get_user_id_from_email(self, user_email: str) -> str:
        """
        Get user ID from email address using Microsoft Graph API.

        Args:
            user_email: User email address

        Returns:
            User ID (object ID)
        """
        try:
            graph_url = f"https://graph.microsoft.com/v1.0/users/{user_email}"
            async with httpx.AsyncClient() as http_client:
                headers = await self._get_headers()
                response = await http_client.get(graph_url, headers=headers)
                response.raise_for_status()
                data = response.json()
                return data.get("id", user_email)
        except Exception as exc:
            logger.warning(
                f"Could not get user ID for {user_email}, using email as fallback: {exc}"
            )
            return user_email

    async def create_subscription(
        self,
        user_email: str,
        notification_url: str,
        expiration_minutes: int = 4320,
    ) -> Dict[str, Any]:
        """
        Create webhook subscription.

        Args:
            user_email: User email address
            notification_url: Webhook notification URL
            expiration_minutes: Subscription expiration in minutes (default 3 days)

        Returns:
            Dictionary containing subscription details
        """
        try:
            logger.info(f"STEP 1: Creating subscription for {user_email}")

            # Get user ID from email
            user_id = await self._get_user_id_from_email(user_email)
            logger.info(f"STEP 2: Using user ID: {user_id}")

            # Calculate expiration (max 3 days for subscriptions)
            expiration_minutes = min(expiration_minutes, 4320)  # Max 3 days
            expiration = datetime.utcnow() + timedelta(minutes=expiration_minutes)

            # Format expiration as ISO 8601 with milliseconds
            expiration_str = expiration.strftime("%Y-%m-%dT%H:%M:%S.0000000Z")

            subscription_data = {
                "changeType": "created,updated",
                "notificationUrl": notification_url,
                "resource": f"/users/{user_id}/mailFolders('inbox')/messages",
                "expirationDateTime": expiration_str,
                "clientState": "secretClientState",
            }

            logger.info(f"STEP 3: Subscription payload: {subscription_data}")

            graph_url = "https://graph.microsoft.com/v1.0/subscriptions"
            async with httpx.AsyncClient() as http_client:
                headers = await self._get_headers()
                response = await http_client.post(
                    graph_url, headers=headers, json=subscription_data
                )

                # Log error details for debugging
                if response.status_code != 201:
                    try:
                        error_body = response.json()
                        logger.error(
                            f"Subscription creation failed with status {response.status_code}: {json.dumps(error_body, indent=2)}"
                        )
                    except:
                        error_body = response.text
                        logger.error(
                            f"Subscription creation failed with status {response.status_code}: {error_body}"
                        )
                    logger.error(
                        f"Request payload: {json.dumps(subscription_data, indent=2)}"
                    )

                response.raise_for_status()
                data = response.json()

            result = {
                "id": data.get("id"),
                "expirationDateTime": data.get("expirationDateTime"),
            }

            logger.info(f"STEP 4: Subscription created with ID: {result['id']}")
            return result
        except Exception as exc:
            logger.error(f"Failed to create subscription: {exc}", exc_info=True)
            raise

    async def renew_subscription(
        self, subscription_id: str, expiration_minutes: int = 4320
    ) -> Dict[str, Any]:
        """
        Renew webhook subscription.

        Args:
            subscription_id: Subscription ID
            expiration_minutes: New expiration in minutes

        Returns:
            Dictionary containing updated subscription details
        """
        try:
            logger.info(f"STEP 1: Renewing subscription {subscription_id}")
            expiration = datetime.utcnow() + timedelta(minutes=expiration_minutes)

            subscription_data = {
                "expirationDateTime": expiration.isoformat() + "Z",
            }

            graph_url = (
                f"https://graph.microsoft.com/v1.0/subscriptions/{subscription_id}"
            )
            async with httpx.AsyncClient() as http_client:
                headers = await self._get_headers()
                response = await http_client.patch(
                    graph_url, headers=headers, json=subscription_data
                )
                response.raise_for_status()
                data = response.json()

            result = {
                "id": data.get("id"),
                "expirationDateTime": data.get("expirationDateTime"),
            }

            logger.info("STEP 2: Subscription renewed")
            return result
        except Exception as exc:
            logger.error(f"Failed to renew subscription: {exc}", exc_info=True)
            raise

    async def delete_subscription(self, subscription_id: str) -> bool:
        """
        Delete webhook subscription.

        Args:
            subscription_id: Subscription ID

        Returns:
            True if deleted, False otherwise
        """
        try:
            logger.info(f"STEP 1: Deleting subscription {subscription_id}")
            graph_url = (
                f"https://graph.microsoft.com/v1.0/subscriptions/{subscription_id}"
            )
            async with httpx.AsyncClient() as http_client:
                headers = await self._get_headers()
                response = await http_client.delete(graph_url, headers=headers)
                response.raise_for_status()
            logger.info("STEP 2: Subscription deleted")
            return True
        except Exception as exc:
            logger.error(f"Failed to delete subscription: {exc}", exc_info=True)
            return False
