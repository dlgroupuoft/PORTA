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
type Role struct {
func GetRoleCount(owner, field, value string) (int64, error) {
func GetRoles(owner string) ([]*Role, error) {
func GetPaginationRoles(owner string, offset, limit int, field, value, sortField, sortOrder string) ([]*Role, error) {
func getRole(owner string, name string) (*Role, error) {
func GetRole(id string) (*Role, error) {
func UpdateRole(id string, role *Role) (bool, error) {
func AddRole(role *Role) (bool, error) {
func AddRoles(roles []*Role) bool {
func AddRolesInBatch(roles []*Role) bool {
func deleteRole(role *Role) (bool, error) {
func DeleteRole(role *Role) (bool, error) {
func (role *Role) GetId() string {
func getRolesByUserInternal(userId string) ([]*Role, error) {
func getRolesByUser(userId string) ([]*Role, error) {
func roleChangeTrigger(oldName string, newName string) error {
			// u = organization/username
func GetMaskedRoles(roles []*Role) []*Role {
// GetAncestorRoles returns a list of roles that contain the given roleIds
func GetAncestorRoles(roleIds ...string) ([]*Role, error) {
	// find all the roles that contain father roles
// containsRole is a helper function to check if a roles is related to any role in the given list roles
func containsRole(role *Role, roleMap map[string]*Role, visited map[string]bool, roleIds ...string) bool {