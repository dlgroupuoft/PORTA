// Copyright 2025 The Casdoor Authors. All Rights Reserved.
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
// GoogleWorkspaceSyncerProvider implements SyncerProvider for Google Workspace API-based syncers
type GoogleWorkspaceSyncerProvider struct {
// InitAdapter initializes the Google Workspace syncer (no database adapter needed)
func (p *GoogleWorkspaceSyncerProvider) InitAdapter() error {
	// Google Workspace syncer doesn't need database adapter
// GetOriginalUsers retrieves all users from Google Workspace API
func (p *GoogleWorkspaceSyncerProvider) GetOriginalUsers() ([]*OriginalUser, error) {
// AddUser adds a new user to Google Workspace (not supported for read-only API)
func (p *GoogleWorkspaceSyncerProvider) AddUser(user *OriginalUser) (bool, error) {
	// Google Workspace syncer is typically read-only
// UpdateUser updates an existing user in Google Workspace (not supported for read-only API)
func (p *GoogleWorkspaceSyncerProvider) UpdateUser(user *OriginalUser) (bool, error) {
	// Google Workspace syncer is typically read-only
// TestConnection tests the Google Workspace API connection
func (p *GoogleWorkspaceSyncerProvider) TestConnection() error {
// Close closes any open connections (no-op for Google Workspace API-based syncer)
func (p *GoogleWorkspaceSyncerProvider) Close() error {
	// Google Workspace syncer doesn't maintain persistent connections
// getAdminService creates and returns a Google Workspace Admin SDK service
func (p *GoogleWorkspaceSyncerProvider) getAdminService() (*admin.Service, error) {
	// syncer.Host should be the admin email (impersonation account)
	// syncer.User should be the service account email or client_email
	// syncer.Password should be the service account private key (JSON key file content)
	// Parse the service account credentials from the password field
	// Parse the JSON key
	// Create JWT config for service account with domain-wide delegation
	// Create Admin SDK service
// getGoogleWorkspaceUsers gets all users from Google Workspace using Admin SDK API
func (p *GoogleWorkspaceSyncerProvider) getGoogleWorkspaceUsers(service *admin.Service) ([]*admin.User, error) {
	// Get the customer ID (use "my_customer" for the domain)
		// Handle pagination
// googleWorkspaceUserToOriginalUser converts Google Workspace user to Casdoor OriginalUser
func (p *GoogleWorkspaceSyncerProvider) googleWorkspaceUserToOriginalUser(gwUser *admin.User) *OriginalUser {
	// Set name fields if Name is not nil
	// Set IsForbidden based on account status
	// Set IsAdmin
	// If display name is empty, construct from first and last name
	// Set CreatedTime from Google or current time
// getGoogleWorkspaceOriginalUsers is the main entry point for Google Workspace syncer
func (p *GoogleWorkspaceSyncerProvider) getGoogleWorkspaceOriginalUsers() ([]*OriginalUser, error) {
	// Get Admin SDK service
	// Get all users from Google Workspace
	// Get all groups and their members to build a user-to-groups mapping
	// This avoids N+1 queries by fetching group memberships upfront
	// Convert Google Workspace users to Casdoor OriginalUser
		// Assign groups from the pre-built map
// buildUserGroupsMap builds a map of user email to group emails by iterating through all groups
// and their members. This is more efficient than querying groups for each user individually.
func (p *GoogleWorkspaceSyncerProvider) buildUserGroupsMap(service *admin.Service) (map[string][]string, error) {
	// Get all groups
	// For each group, get its members and populate the user-to-groups map
		// Add this group to each member's group list
// getGroupMembers retrieves all members of a specific group
func (p *GoogleWorkspaceSyncerProvider) getGroupMembers(service *admin.Service, groupId string) ([]*admin.Member, error) {
		// Handle pagination
// GetOriginalGroups retrieves all groups from Google Workspace
func (p *GoogleWorkspaceSyncerProvider) GetOriginalGroups() ([]*OriginalGroup, error) {
	// Get Admin SDK service
	// Get all groups from Google Workspace
	// Convert Google Workspace groups to Casdoor OriginalGroup
// GetOriginalUserGroups retrieves the group IDs that a user belongs to
func (p *GoogleWorkspaceSyncerProvider) GetOriginalUserGroups(userId string) ([]string, error) {
	// Get Admin SDK service
	// Get groups for the user
		// Handle pagination
// getGoogleWorkspaceGroups gets all groups from Google Workspace using Admin SDK API
func (p *GoogleWorkspaceSyncerProvider) getGoogleWorkspaceGroups(service *admin.Service) ([]*admin.Group, error) {
	// Get the customer ID (use "my_customer" for the domain)
		// Handle pagination
// googleWorkspaceGroupToOriginalGroup converts Google Workspace group to Casdoor OriginalGroup
func (p *GoogleWorkspaceSyncerProvider) googleWorkspaceGroupToOriginalGroup(gwGroup *admin.Group) *OriginalGroup {