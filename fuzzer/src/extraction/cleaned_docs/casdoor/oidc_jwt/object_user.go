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
func InitUserManager() {
type User struct {
type Userinfo struct {
type ManagedAccount struct {
type MfaAccount struct {
type Address struct {
type FaceId struct {
func GetUserFieldStringValue(user *User, fieldName string) (bool, string, error) {
func GetGlobalUserCount(field, value string) (int64, error) {
func GetGlobalUsers() ([]*User, error) {
func GetGlobalUsersWithFilter(cond builder.Cond) ([]*User, error) {
func GetPaginationGlobalUsers(offset, limit int, field, value, sortField, sortOrder string) ([]*User, error) {
func GetUserCount(owner, field, value string, groupName string) (int64, error) {
func GetOnlineUserCount(owner string, isOnline int) (int64, error) {
func GetUsers(owner string) ([]*User, error) {
func GetUsersWithFilter(owner string, cond builder.Cond) ([]*User, error) {
func GetUsersByTagWithFilter(owner string, tag string, cond builder.Cond) ([]*User, error) {
func GetSortedUsers(owner string, sorter string, limit int) ([]*User, error) {
func GetPaginationUsers(owner string, offset, limit int, field, value, sortField, sortOrder string, groupName string) ([]*User, error) {
func getUser(owner string, name string) (*User, error) {
func getUserById(owner string, id string) (*User, error) {
func getUserByWechatId(owner string, wechatOpenId string, wechatUnionId string) (*User, error) {
func GetUserByEmail(owner string, email string) (*User, error) {
func GetUserByWebauthID(webauthId string) (*User, error) {
func GetUserByEmailOnly(email string) (*User, error) {
func GetUserByPhone(owner string, phone string) (*User, error) {
func GetUserByPhoneOnly(phone string) (*User, error) {
func GetUserByUserId(owner string, userId string) (*User, error) {
func GetUserByUserIdOnly(userId string) (*User, error) {
func GetUserByInvitationCode(owner string, invitationCode string) (*User, error) {
func GetUserByAccessKey(accessKey string) (*User, error) {
func GetUser(id string) (*User, error) {
func GetUserNoCheck(id string) (*User, error) {
func GetMaskedUser(user *User, isAdminOrSelf bool, errs ...error) (*User, error) {
		// Mask per-provider OAuth tokens in Properties
				// More specific pattern matching to avoid masking unrelated properties
func GetFilteredUser(user *User, isAdmin bool, isAdminOrSelf bool, accountItems []*AccountItem) (*User, error) {
func GetMaskedUsers(users []*User, errs ...error) ([]*User, error) {
func getLastUser(owner string) (*User, error) {
func UpdateUser(id string, user *User, columns []string, isAdmin bool) (bool, error) {
	// Auto-upgrade guest users when they update their username or password
		// Check if username is being changed from the generated guest username
		// Check if password is being updated (not the placeholder ***)
			// Upgrade to normal user
			// Ensure tag is included in the update columns
func updateUser(id string, user *User, columns []string) (int64, error) {
	// Ensure hash column is included in updates when columns are specified
func UpdateUserForAllFields(id string, user *User) (bool, error) {
func AddUser(user *User, lang string) (bool, error) {
func AddUsers(users []*User) (bool, error) {
	// organization := GetOrganizationByUser(users[0])
		// this function is only used for syncer or batch upload, so no need to encrypt the password
		// user.UpdateUserPassword(organization)
func AddUsersInBatch(users []*User) (bool, error) {
func deleteUser(user *User) (bool, error) {
func DeleteUser(user *User) (bool, error) {
	// Forced offline the user first
func GetUserInfo(user *User, scope string, aud string, host string) (*Userinfo, error) {
		// resp.EmailVerified = user.EmailVerified
func LinkUserAccount(user *User, field string, value string) (bool, error) {
func (user *User) GetId() string {
func (user *User) GetFriendlyName() string {
func isUserIdGlobalAdmin(userId string) bool {
func ExtendUserWithRolesAndPermissions(user *User) (err error) {
func DeleteGroupForUser(user string, group string) (bool, error) {
func userChangeTrigger(oldName string, newName string) error {
			// u = organization/username
			// u = organization/username
func (user *User) IsMfaEnabled() bool {
func (user *User) GetPreferredMfaProps(masked bool) *MfaProps {
func AddUserKeys(user *User, isAdmin bool) (bool, error) {
func (user *User) IsApplicationAdmin(application *Application) bool {
func (user *User) IsGlobalAdmin() bool {
func (user *User) CheckUserFace(faceIdImage []string, provider *Provider) (bool, error) {
func (user *User) GetUserFullGroupPath() ([]string, error) {
func GenerateIdForNewUser(application *Application) (string, error) {
func UpdateUserBalance(owner string, name string, balance float64, currency string, lang string) error {
	// Convert the balance amount from transaction currency to user's balance currency
		// Get organization's balance currency as fallback
	// Calculate new balance
	// Check balance credit limit
	// User.BalanceCredit takes precedence over Organization.BalanceCredit
		// Get organization's balance credit as fallback
	// Validate new balance against credit limit