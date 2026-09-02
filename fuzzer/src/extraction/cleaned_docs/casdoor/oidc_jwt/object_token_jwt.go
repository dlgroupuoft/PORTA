// Copyright 2021 The Casdoor Authors. All Rights Reserved.
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
type Claims struct {
	// the `azp` (Authorized Party) claim. Optional. See https://openid.net/specs/openid-connect-core-1_0.html#IDToken
type UserShort struct {
type UserStandard struct {
type UserWithoutThirdIdp struct {
	// WebauthnCredentials []webauthn.Credential `xorm:"webauthnCredentials blob" json:"webauthnCredentials"`
	// MultiFactorAuths    []*MfaProps           `xorm:"-" json:"multiFactorAuths,omitempty"`
type ClaimsShort struct {
type OIDCAddress struct {
type ClaimsWithoutThirdIdp struct {
func getShortUser(user *User) *UserShort {
func getStandardUser(user *User) *UserStandard {
func getUserWithoutThirdIdp(user *User) *UserWithoutThirdIdp {
func getShortClaims(claims Claims) ClaimsShort {
func getClaimsWithoutThirdIdp(claims Claims) ClaimsWithoutThirdIdp {
// getUserFieldValue gets the value of a user field by name, handling special cases like Roles and Permissions
func getUserFieldValue(user *User, fieldName string) (interface{}, bool) {
	// Handle special fields that need conversion
	// Handle Properties fields (e.g., Properties.my_field)
	// Use reflection to get the field value
func getClaimsCustom(claims Claims, tokenField []string, tokenAttributes []*JwtItem) jwt.MapClaims {
	// Always include standard JWT registered claims
	// Always include tokenType (essential metadata)
	// Always include azp if present (authorized party)
	// Always include nonce and scope as they are built-in OAuth/OIDC fields (even if empty)
	// Create a map for quick lookup of selected token fields
	// Only include signinMethod and provider if they are explicitly selected in tokenFields
		// If Category is "Existing Field", get the actual field value from the user
			// Default behavior: use replaceAttributeValue for "Static Value" or empty category
func refineUser(user *User) *User {
func generateJwtToken(application *Application, user *User, provider string, signinMethod string, nonce string, scope string, resource string, host string) (string, string, string, error) {
		// FIXME: A workaround for custom claim by reusing `tag` in user info
	// RFC 8707: Use resource as audience when provided
	// the JWT token length in "JWT-Empty" mode will be very short, as User object only has two properties: owner and name
		// RSA private key
		// ES private key
		// Ed private key
func ParseJwtTokenWithoutValidation(token string) (*jwt.Token, error) {
func ParseJwtToken(token string, cert *Cert) (*Claims, error) {
			// RSA certificate
			// ES certificate
func ParseJwtTokenByApplication(token string, application *Application) (*Claims, error) {