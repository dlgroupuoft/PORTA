// Copyright 2024 The Casdoor Authors. All Rights Reserved.
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
type Code struct {
type TokenWrapper struct {
type TokenError struct {
type IntrospectionResponse struct {
type DeviceAuthCache struct {
type DeviceAuthResponse struct {
// validateResourceURI validates that the resource parameter is a valid absolute URI
// according to RFC 8707 Section 2
func validateResourceURI(resource string) error {
	// RFC 8707: The resource parameter must be an absolute URI
func ExpireTokenByAccessToken(accessToken string) (bool, *Application, *Token, error) {
func CheckOAuthLogin(clientId string, responseType string, redirectUri string, scope string, state string, lang string) (string, *Application, error) {
	// Mask application for /api/get-app-login
func GetOAuthCode(userId string, clientId string, provider string, signinMethod string, responseType string, redirectUri string, scope string, state string, nonce string, challenge string, resource string, host string, lang string) (*Code, error) {
	// Expand regex/wildcard scopes to concrete scope names.
	// Validate resource parameter (RFC 8707)
func GetOAuthToken(grantType string, clientId string, clientSecret string, code string, verifier string, scope string, nonce string, username string, password string, host string, refreshToken string, tag string, avatar string, lang string, subjectToken string, subjectTokenType string, assertion string, clientAssertion string, clientAssertionType string, audience string, resource string) (interface{}, error) {
	// Check if grantType is allowed in the current application
		// Wechat Mini Program
func RefreshToken(application *Application, grantType string, refreshToken string, scope string, clientId string, clientSecret string, host string) (interface{}, error) {
	// check parameters
	// check whether the refresh token is valid, and has not expired.
	// check if the token has been invalidated (e.g., by SSO logout)
	// generate a new token
// PkceChallenge: base64-URL-encoded SHA256 hash of verifier, per rfc 7636
func pkceChallenge(verifier string) string {
// IsGrantTypeValid
// Check if grantType is allowed in the current application
// authorization_code is allowed by default
func IsGrantTypeValid(method string, grantTypes []string) bool {
// isRegexScope returns true if the scope string contains regex metacharacters.
func isRegexScope(scope string) bool {
// IsScopeValidAndExpand expands any regex patterns in the space-separated scope string
// against the application's configured scopes. Literal scopes are kept as-is
// after verifying they exist in the allowed list. Regex scopes are matched
// against every allowed scope name; all matches replace the pattern.
// If the application has no defined scopes, the original scope string is
// returned unchanged (backward-compatible behaviour).
// Returns the expanded scope string and whether the scope is valid.
func IsScopeValidAndExpand(scope string, application *Application) (string, bool) {
		// Try exact match first.
		// Not an exact match – if it looks like a regex, try pattern matching.
		// Treat as regex pattern – must be a valid regex and match ≥ 1 scope.
// IsScopeValid checks whether all space-separated scopes in the scope string
// are defined in the application's Scopes list (including regex expansion).
// If the application has no defined scopes, every scope is considered valid
// (backward-compatible behaviour).
func IsScopeValid(scope string, application *Application) bool {
// createGuestUserToken creates a new guest user and returns a token for them
func createGuestUserToken(application *Application, clientSecret string, verifier string) (*Token, *TokenError, error) {
	// Verify client secret if provided
	// Generate a unique guest username
	// Generate a random password for the guest user
	// Get organization
	// Get initial score
	// Generate a unique user ID within the confines of the application
		// If we fail to generate a unique user ID, we can fallback to a random ID
	// Create the guest user
	// Add the user
	// Extend user with roles and permissions
	// Generate JWT token
	// Create token object
// generateGuestUsername generates a unique username for guest users
func generateGuestUsername() string {
		// Fallback to a timestamp-based unique ID if UUID generation fails
// GetAuthorizationCodeToken
// Authorization code flow
func GetAuthorizationCodeToken(application *Application, clientSecret string, code string, verifier string, resource string) (*Token, *TokenError, error) {
	// Handle guest user creation
		// anti replay attacks
		// when using PKCE, the Client Secret can be empty,
		// but if it is provided, it must be accurate.
	// RFC 8707: Validate resource parameter matches the one in the authorization request
		// code must be used within 5 minutes
// GetPasswordToken
// Resource Owner Password Credentials flow
func GetPasswordToken(application *Application, username string, password string, scope string, host string) (*Token, *TokenError, error) {
		// For OAuth users who don't have a password set, they cannot use password grant type
// GetClientCredentialsToken
// Client Credentials flow
func GetClientCredentialsToken(application *Application, clientSecret string, scope string, host string) (*Token, *TokenError, error) {
// GetImplicitToken
// Implicit flow
func GetImplicitToken(application *Application, username string, scope string, nonce string, host string) (*Token, *TokenError, error) {
// GetJwtBearerToken
// RFC 7523
func GetJwtBearerToken(application *Application, assertion string, scope string, nonce string, host string) (*Token, *TokenError, error) {
func ValidateJwtAssertion(clientAssertion string, application *Application, host string) (bool, *Claims, error) {
func ValidateClientAssertion(clientAssertion string, host string) (bool, *Application, error) {
// GetTokenByUser
// Implicit flow
func GetTokenByUser(application *Application, user *User, scope string, nonce string, host string) (*Token, error) {
// GetWechatMiniProgramToken
// Wechat Mini Program flow
func GetWechatMiniProgramToken(application *Application, code string, host string, username string, avatar string, lang string) (*Token, *TokenError, error) {
		// Add new user
		// Generate a unique user ID within the confines of the application
			// If we fail to generate a unique user ID, we can fallback to a random ID
// GetTokenExchangeToken
// Token Exchange Grant (RFC 8693)
// Exchanges a subject token for a new token with different audience or scope
func GetTokenExchangeToken(application *Application, clientSecret string, subjectToken string, subjectTokenType string, audience string, scope string, host string) (*Token, *TokenError, error) {
	// Verify client secret
	// Validate subject_token parameter
	// Validate subject_token_type parameter
	// RFC 8693 defines standard token type identifiers
	// Support common token types
	// Get certificate for token validation
	// Parse and validate the subject token
	// Get the user from the subject token
	// Handle scope parameter
	// If scope is not provided, use the scope from the subject token
	// If scope is provided, it should be a subset of the subject token's scope (downscoping)
		// Validate scope downscoping (basic implementation)
		// In a production environment, you would implement more sophisticated scope validation
	// Extend user with roles and permissions
	// Generate new JWT token
	// Create token object
func GetAccessTokenByUser(user *User, host string) (string, error) {