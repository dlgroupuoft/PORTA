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
func CheckUserSignup(application *Application, organization *Organization, authForm *form.AuthForm, lang string) string {
				// if !isValidRealName(authForm.Name) {
				//	return i18n.Translate(lang, "check:DisplayName is not valid real name")
				// }
func CheckInvitationCode(application *Application, organization *Organization, authForm *form.AuthForm, lang string) (*Invitation, string) {
func CheckInvitationDefaultCode(code string, defaultCode string, lang string) error {
func checkSigninErrorTimes(user *User, lang string) error {
		// deny the login if the error times is greater than the limit and the last login time is less than the duration
		// reset the error times
func CheckPassword(user *User, password string, lang string, options ...bool) error {
	// check the login error times
func CheckPasswordComplexityByOrg(organization *Organization, password string, lang string) string {
func CheckPasswordComplexity(user *User, password string, lang string) string {
func CheckLdapUserPassword(user *User, password string, lang string, options ...bool) error {
	// check the login error times
func CheckUserPassword(organization string, username string, password string, lang string, options ...bool) (*User, error) {
	// Prevent direct login for guest users without upgrading
		// only for LDAP users
func CheckUserPermission(requestUserId, userId string, strict bool, lang string) (bool, error) {
func CheckApiPermission(userId string, organization string, path string, method string) (bool, error) {
	// Deny-override, if one deny is found, then deny
	// For no-allow and no-deny condition
	// If only allow permissions exist, we suppose it's Deny-by-default, aka no-allow means deny
	// Otherwise, it's Allow-by-default, aka no-deny means allow
func CheckLoginPermission(userId string, application *Application) (bool, error) {
	// Deny-override, if one deny is found, then deny
	// For no-allow and no-deny condition
	// If only allow permissions exist, we suppose it's Deny-by-default, aka no-allow means deny
	// Otherwise, it's Allow-by-default, aka no-deny means allow
func CheckUsername(username string, lang string) string {
	// https://stackoverflow.com/questions/58726546/github-username-convention-using-regex
func CheckUsernameWithEmail(username string, lang string) string {
	// https://stackoverflow.com/questions/58726546/github-username-convention-using-regex
func CheckUpdateUser(oldUser, user *User, lang string) string {
func CheckToEnableCaptcha(application *Application, organization, username string, clientIp string) (bool, error) {