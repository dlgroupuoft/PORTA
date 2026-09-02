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
type Permission struct {
func GetPermissionCount(owner, field, value string) (int64, error) {
func GetPermissions(owner string) ([]*Permission, error) {
func GetPaginationPermissions(owner string, offset, limit int, field, value, sortField, sortOrder string) ([]*Permission, error) {
func getPermission(owner string, name string) (*Permission, error) {
func GetPermission(id string) (*Permission, error) {
// checkPermissionValid verifies if the permission is valid
func checkPermissionValid(permission *Permission) error {
func UpdatePermission(id string, permission *Permission) (bool, error) {
		// if oldPermission.Adapter != "" && oldPermission.Adapter != permission.Adapter {
		// 	isEmpty, _ := ormer.Engine.IsTableEmpty(oldPermission.Adapter)
		// 	if isEmpty {
		// 		err = ormer.Engine.DropTables(oldPermission.Adapter)
		// 		if err != nil {
		// 			return false, err
		// 		}
		// 	}
		// }
func AddPermission(permission *Permission) (bool, error) {
func AddPermissions(permissions []*Permission) (bool, error) {
		// add using for loop
func AddPermissionsInBatch(permissions []*Permission) (bool, error) {
func deletePermission(permission *Permission) (bool, error) {
func DeletePermission(permission *Permission) (bool, error) {
		// if permission.Adapter != "" && permission.Adapter != "permission_rule" {
		// 	isEmpty, _ := ormer.Engine.IsTableEmpty(permission.Adapter)
		// 	if isEmpty {
		// 		err = ormer.Engine.DropTables(permission.Adapter)
		// 		if err != nil {
		// 			return false, err
		// 		}
		// 	}
		// }
func getPermissionsByUser(userId string) ([]*Permission, error) {
func GetPermissionsByRole(roleId string) ([]*Permission, error) {
func GetPermissionsByResource(resourceId string) ([]*Permission, error) {
func getPermissionsAndRolesByUser(userId string) ([]*Permission, []*Role, error) {
func GetPermissionsBySubmitter(owner string, submitter string) ([]*Permission, error) {
func GetPermissionsByModel(owner string, model string) ([]*Permission, error) {
func GetMaskedPermissions(permissions []*Permission) []*Permission {
// GroupPermissionsByModelAdapter group permissions by model and adapter.
// Every model and adapter will be a key, and the value is a list of permission ids.
// With each list of permission ids have the same key, we just need to init the
// enforcer and do the enforce/batch-enforce once (with list of permission ids
// as the policyFilter when the enforcer load policy).
func GroupPermissionsByModelAdapter(permissions []*Permission) map[string][]string {
func (p *Permission) GetId() string {
func (p *Permission) GetModelAndAdapter() string {
func (p *Permission) isUserHit(name string) bool {
func (p *Permission) isRoleHit(userId string) bool {
func (p *Permission) isResourceHit(name string) bool {