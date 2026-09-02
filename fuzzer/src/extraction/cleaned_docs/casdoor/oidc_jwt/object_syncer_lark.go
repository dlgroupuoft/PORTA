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
// LarkSyncerProvider implements SyncerProvider for Lark API-based syncers
type LarkSyncerProvider struct {
// InitAdapter initializes the Lark syncer (no database adapter needed)
func (p *LarkSyncerProvider) InitAdapter() error {
	// Lark syncer doesn't need database adapter
// GetOriginalUsers retrieves all users from Lark API
func (p *LarkSyncerProvider) GetOriginalUsers() ([]*OriginalUser, error) {
// AddUser adds a new user to Lark (not supported for read-only API)
func (p *LarkSyncerProvider) AddUser(user *OriginalUser) (bool, error) {
	// Lark syncer is typically read-only
// UpdateUser updates an existing user in Lark (not supported for read-only API)
func (p *LarkSyncerProvider) UpdateUser(user *OriginalUser) (bool, error) {
	// Lark syncer is typically read-only
// TestConnection tests the Lark API connection
func (p *LarkSyncerProvider) TestConnection() error {
// Close closes any open connections (no-op for Lark API-based syncer)
func (p *LarkSyncerProvider) Close() error {
	// Lark syncer doesn't maintain persistent connections
type LarkAccessTokenResp struct {
type LarkUser struct {
type LarkAvatar struct {
type LarkStatus struct {
type LarkUserListResp struct {
type LarkDeptListResp struct {
// getLarkDomain returns the Lark API domain based on whether global endpoint is used
func (p *LarkSyncerProvider) getLarkDomain() string {
	// syncer.Host can be used to specify custom endpoint
	// If empty, default to global endpoint (larksuite.com)
// getLarkAccessToken gets access token from Lark API
func (p *LarkSyncerProvider) getLarkAccessToken() (string, error) {
	// syncer.User should be the app_id
	// syncer.Password should be the app_secret
// getLarkDepartments gets all department IDs from Lark API
func (p *LarkSyncerProvider) getLarkDepartments(accessToken string) ([]string, error) {
// getLarkUsersFromDept gets users from a specific department
func (p *LarkSyncerProvider) getLarkUsersFromDept(accessToken string, deptId string) ([]*LarkUser, error) {
// postJSON sends a POST request with JSON body
func (p *LarkSyncerProvider) postJSON(url string, data interface{}) ([]byte, error) {
// getWithAuth sends a GET request with authorization header
func (p *LarkSyncerProvider) getWithAuth(url string, accessToken string) ([]byte, error) {
// getLarkUsers gets all users from Lark API
func (p *LarkSyncerProvider) getLarkUsers() ([]*OriginalUser, error) {
	// Get access token
	// Get all departments
	// Get users from all departments (deduplicate by user_id)
			// Deduplicate users by user_id
	// Convert Lark users to Casdoor OriginalUser
// larkUserToOriginalUser converts Lark user to Casdoor OriginalUser
func (p *LarkSyncerProvider) larkUserToOriginalUser(larkUser *LarkUser) *OriginalUser {
	// Use user_id as name, fallback to union_id or open_id
	// Set avatar if available
	// Set gender
	// Set IsForbidden based on status
	// User is forbidden if frozen, resigned, not activated, or exited
	// Set CreatedTime to current time if not set
// GetOriginalGroups retrieves all groups from Lark (not implemented yet)
func (p *LarkSyncerProvider) GetOriginalGroups() ([]*OriginalGroup, error) {
	// TODO: Implement Lark group sync
// GetOriginalUserGroups retrieves the group IDs that a user belongs to (not implemented yet)
func (p *LarkSyncerProvider) GetOriginalUserGroups(userId string) ([]string, error) {
	// TODO: Implement Lark user group membership sync