// Copyright 2023 The Casdoor Authors. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
package object
func getNotificationClient(provider *Provider) (notify.Notifier, error) {
func SendNotification(provider *Provider, content string) error {
// SsoLogoutNotification represents the structure of a session-level SSO logout notification
// This includes session information and a signature for authentication
type SsoLogoutNotification struct {
	// User information
	// Event type
	// Session-level information for targeted logout
	// Authentication fields to prevent malicious logout requests
// GetTokensByUser retrieves all tokens for a specific user
func GetTokensByUser(owner, username string) ([]*Token, error) {
// generateLogoutSignature generates an HMAC-SHA256 signature for the logout notification
// The signature is computed over the critical fields to prevent tampering
func generateLogoutSignature(clientSecret string, owner string, name string, nonce string, timestamp int64, sessionIds []string, accessTokenHashes []string) string {
	// Create a deterministic string from all fields that need to be verified
	// Use strings.Join to avoid trailing separators and improve performance
// SendSsoLogoutNotifications sends logout notifications to all notification providers
// configured in the user's signup application
func SendSsoLogoutNotifications(user *User, sessionIds []string, tokens []*Token) error {
	// If user's signup application is empty, don't send notifications
	// Get the user's signup application
	// Extract access token hashes from tokens
	// Generate nonce and timestamp for replay protection
	// Generate signature using the application's client secret
	// Prepare the notification data
	// Send notifications to all notification providers in the signup application
		// Only send to notification providers
		// Send the notification using the provider from the providerItem
// VerifySsoLogoutSignature verifies the signature of an SSO logout notification
// This should be called by applications receiving logout notifications
func VerifySsoLogoutSignature(clientSecret string, notification *SsoLogoutNotification) bool {