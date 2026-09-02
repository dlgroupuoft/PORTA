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
// formatUserPhone processes phone number for a user based on their CountryCode
func formatUserPhone(u *User) {
	// 1. Normalize hint (e.g., "China" -> "CN") for the parser
	// 2. Try parsing (Strictly using countryHint from LDAP)
		// Store a clean national number (digits only, without country prefix)
type LdapConn struct {
//type ldapGroup struct {
//	GidNumber string
//	Cn        string
//}
type LdapUser struct {
	// Gcn                   string
type LdapGroup struct {
func (ldap *Ldap) GetLdapConn() (c *LdapConn, err error) {
func (l *LdapConn) Close() {
func isMicrosoftAD(Conn *goldap.Conn) (bool, error) {
	type ldapServerType struct {
func (l *LdapConn) GetLdapUsers(ldapServer *Ldap) ([]LdapUser, error) {
// GetLdapGroups fetches LDAP groups and organizational units
func (l *LdapConn) GetLdapGroups(ldapServer *Ldap) ([]LdapGroup, error) {
	// Search for LDAP groups (groupOfNames, groupOfUniqueNames, posixGroup)
	// Add Active Directory group filter
	// Build combined filter
		// Groups might not exist, which is okay
		// Use cn as name if name is not set
		// Parse parent DN from the entry DN
	// Also fetch organizational units as groups
			// Parse parent DN from the entry DN
// getParentDn extracts the parent DN from a full DN
func getParentDn(dn string) string {
	// Split DN by comma
	// Remove the first component (the current node) and rejoin
// parseDnToGroupName converts a DN to a group name
func parseDnToGroupName(dn string) string {
	// Extract the CN or OU from the DN
	// Extract value after = sign
func AutoAdjustLdapUser(users []LdapUser) []LdapUser {
func SyncLdapUsers(owner string, syncUsers []LdapUser, ldapId string) (existUsers []LdapUser, failedUsers []LdapUser, err error) {
			// Assign user to groups based on memberOf attribute
			// Extract group names from memberOf DNs
			// Trigger webhook for LDAP user sync
// SyncLdapGroups syncs LDAP groups/OUs to Casdoor groups with hierarchy
func SyncLdapGroups(owner string, ldapGroups []LdapGroup, ldapId string) (newGroups int, updatedGroups int, err error) {
	// Create a map of DN to group for quick lookup
	// Get existing groups for this organization
	// Process groups in hierarchical order (parents before children)
		// Generate group name from DN
		// Determine parent
			// Process parent first
		// Check if group already exists
			// Update existing group
			// Create new group
	// Process all groups
			// Log error but continue processing other groups
// dnToGroupName converts an LDAP DN to a Casdoor group name
func dnToGroupName(owner, dn string) string {
	// Parse DN to extract meaningful components
	// Build a hierarchical name from DN components (excluding DC parts)
		// Skip DC (domain component) parts
		// Extract value after = sign
	// Reverse to get top-down hierarchy
	// Join with underscore to create a unique group name
	// Sanitize group name - replace invalid characters with underscores
	// Keep only alphanumeric characters, underscores, and hyphens
	// Remove consecutive underscores and trim
func GetExistUuids(owner string, uuids []string) ([]string, error) {
	// PostgreSQL only supports up to 65535 parameters per query, so we batch the uuids
func ResetLdapPassword(user *User, oldPassword string, newPassword string, lang string) error {
func (ldapUser *LdapUser) buildLdapUserName(owner string) (string, error) {
func (ldapUser *LdapUser) buildLdapDisplayName() string {
func (ldapUser *LdapUser) GetLdapUuid() string {
func (ldap *Ldap) buildAuthFilterString(user *User) string {
func (user *User) getFieldFromLdapAttribute(attribute string) string {