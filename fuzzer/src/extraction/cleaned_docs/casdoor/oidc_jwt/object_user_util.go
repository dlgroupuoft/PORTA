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
func GetUserByField(organizationName string, field string, value string) (*User, error) {
func HasUserByField(organizationName string, field string, value string) bool {
func GetUserByFields(organization string, field string) (*User, error) {
	// check username
	// check email
	// check phone
	// check user ID
	// check ID card
func SetUserField(user *User, field string, value string) (bool, error) {
func GetUserField(user *User, field string) string {
	// https://socketloop.com/tutorials/golang-how-to-get-struct-field-and-value-by-name
func setUserProperty(user *User, field string, value string) {
func getUserProperty(user *User, field string) string {
func getUserExtraProperty(user *User, providerType, key string) (string, error) {
// getOAuthTokenPropertyKey returns the property key for storing OAuth tokens
func getOAuthTokenPropertyKey(providerType string, tokenType string) string {
// GetUserOAuthAccessToken retrieves the OAuth access token for a specific provider
func GetUserOAuthAccessToken(user *User, providerType string) string {
// GetUserOAuthRefreshToken retrieves the OAuth refresh token for a specific provider
func GetUserOAuthRefreshToken(user *User, providerType string) string {
func SetUserOAuthProperties(organization *Organization, user *User, providerType string, userInfo *idp.UserInfo, token *oauth2.Token, userMapping ...map[string]string) (bool, error) {
	// Store the original OAuth provider token if available
		// Store tokens per provider in Properties map
		// Also update the legacy fields for backward compatibility
	// Apply custom user mapping from provider configuration
		// Save extra info as json string
func applyUserMapping(user *User, extraClaims map[string]string, userMapping map[string]string) {
	// Map of user fields that can be set from IDP claims
		// Skip standard fields that are already handled
		// Get value from extra claims
		// Map to user fields based on field name
func getUserRoleNames(user *User) (res []string) {
func getUserPermissionNames(user *User) (res []string) {
func ClearUserOAuthProperties(user *User, providerType string) (bool, error) {
func userVisible(isAdmin bool, item *AccountItem) bool {
func CheckPermissionForUpdateUser(oldUser, newUser *User, isAdmin bool, allowDisplayNameEmpty bool, lang string) (bool, string) {
	// The password is *** when not modified
		// Skip nil items - these occur when a field doesn't have a corresponding
		// account item configuration, meaning no validation rules apply
func (user *User) GetCountryCode(countryCode string) string {
func (user *User) IsAdminUser() bool {
func IsAppUser(userId string) bool {
func setReflectAttr[T any](fieldValue *reflect.Value, fieldString string) error {
func StringArrayToStruct[T any](stringArray [][]string) ([]*T, error) {
func replaceAttributeValue(user *User, value string) []string {
func replaceAttributeValues(val string, replaceVal string, values []string) []string {
func replaceAttributeValuesWithList(val string, replaceVals []string, values []string) []string {
// TriggerWebhookForUser triggers a webhook for user operations (add, update, delete)
// action: the action type, e.g., "new-user", "update-user", "delete-user"
// user: the user object
func TriggerWebhookForUser(action string, user *User) {