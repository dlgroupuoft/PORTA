// Copyright 2026 The Casdoor Authors. All Rights Reserved.
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
// DingtalkSyncerProvider implements SyncerProvider for DingTalk API-based syncers
type DingtalkSyncerProvider struct {
// InitAdapter initializes the DingTalk syncer (no database adapter needed)
func (p *DingtalkSyncerProvider) InitAdapter() error {
	// DingTalk syncer doesn't need database adapter
// GetOriginalUsers retrieves all users from DingTalk API
func (p *DingtalkSyncerProvider) GetOriginalUsers() ([]*OriginalUser, error) {
// AddUser adds a new user to DingTalk (not supported for read-only API)
func (p *DingtalkSyncerProvider) AddUser(user *OriginalUser) (bool, error) {
	// DingTalk syncer is typically read-only
// UpdateUser updates an existing user in DingTalk (not supported for read-only API)
func (p *DingtalkSyncerProvider) UpdateUser(user *OriginalUser) (bool, error) {
	// DingTalk syncer is typically read-only
// TestConnection tests the DingTalk API connection
func (p *DingtalkSyncerProvider) TestConnection() error {
// Close closes any open connections (no-op for DingTalk API-based syncer)
func (p *DingtalkSyncerProvider) Close() error {
	// DingTalk syncer doesn't maintain persistent connections
type DingtalkAccessTokenResp struct {
type DingtalkUser struct {
type DingtalkUserListResp struct {
type DingtalkResult struct {
type DingtalkDeptListResp struct {
type DingtalkDepartment struct {
type DingtalkDeptDetailResp struct {
// getDingtalkAccessToken gets access token from DingTalk API
func (p *DingtalkSyncerProvider) getDingtalkAccessToken() (string, error) {
	// syncer.User should be the appKey
	// syncer.Password should be the appSecret
// getDingtalkDepartments gets all department IDs from DingTalk API recursively
func (p *DingtalkSyncerProvider) getDingtalkDepartments(accessToken string) ([]int64, error) {
// getDingtalkDepartmentsRecursive recursively fetches all departments starting from parentDeptId
func (p *DingtalkSyncerProvider) getDingtalkDepartmentsRecursive(accessToken string, parentDeptId int64) ([]int64, error) {
	// Start with the parent department itself
	// Recursively fetch all child departments
// getDingtalkDepartmentDetails gets detailed department information
func (p *DingtalkSyncerProvider) getDingtalkDepartmentDetails(accessToken string, deptId int64) (*DingtalkDepartment, error) {
// getDingtalkUsersFromDept gets users from a specific department
func (p *DingtalkSyncerProvider) getDingtalkUsersFromDept(accessToken string, deptId int64) ([]*DingtalkUser, error) {
// getDingtalkUserDetails gets detailed user information
func (p *DingtalkSyncerProvider) getDingtalkUserDetails(accessToken string, userId string) (*DingtalkUser, error) {
// postJSON sends a POST request with JSON body
func (p *DingtalkSyncerProvider) postJSON(url string, data map[string]interface{}) ([]byte, error) {
// getDingtalkUsers gets all users from DingTalk API
func (p *DingtalkSyncerProvider) getDingtalkUsers() ([]*OriginalUser, error) {
	// Get access token
	// Get all departments
	// Get users from all departments (deduplicate by userid)
			// Deduplicate users by userid
				// Get detailed user information
					// Use basic user info if details fail
	// Convert DingTalk users to Casdoor OriginalUser
// getDingtalkUserFieldValue extracts a field value from DingtalkUser by field name
func (p *DingtalkSyncerProvider) getDingtalkUserFieldValue(dingtalkUser *DingtalkUser, fieldName string) string {
		// Invert the boolean because active=true means NOT forbidden
// dingtalkUserToOriginalUser converts DingTalk user to Casdoor OriginalUser
func (p *DingtalkSyncerProvider) dingtalkUserToOriginalUser(dingtalkUser *DingtalkUser) *OriginalUser {
	// Apply TableColumns mapping if configured
		// Fallback to default mapping for backward compatibility
	// Add department IDs to Groups field
	// Set CreatedTime to current time if not set
// GetOriginalGroups retrieves all groups (departments) from DingTalk
func (p *DingtalkSyncerProvider) GetOriginalGroups() ([]*OriginalGroup, error) {
	// Get access token
	// Get all department IDs
	// Get detailed information for each department
			// Log error but continue with other departments
// dingtalkDepartmentToOriginalGroup converts DingTalk department to Casdoor OriginalGroup
func (p *DingtalkSyncerProvider) dingtalkDepartmentToOriginalGroup(dept *DingtalkDepartment) *OriginalGroup {
	// Convert department ID to string for group ID
// GetOriginalUserGroups retrieves the group (department) IDs that a user belongs to
func (p *DingtalkSyncerProvider) GetOriginalUserGroups(userId string) ([]string, error) {
	// Get access token
	// Get detailed user information which includes department list
	// Convert department IDs to strings