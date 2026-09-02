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
func getPermissionEnforcer(p *Permission, permissionIDs ...string) (*casbin.Enforcer, error) {
	// Init an enforcer instance without specifying a model or adapter.
	// If you specify an adapter, it will load all policies, which is a
	// heavy process that can slow down the application.
func (p *Permission) setEnforcerAdapter(enforcer *casbin.Enforcer) error {
func (p *Permission) setEnforcerModel(enforcer *casbin.Enforcer) error {
	// TODO: return error if permissionModel is nil.
func getPolicies(permission *Permission) [][]string {
func getRolesInRole(roleId string, visited map[string]struct{}) ([]*Role, error) {
func getGroupingPolicies(permission *Permission) ([][]string, error) {
func addPolicies(permission *Permission) error {
func removePolicies(permission *Permission) error {
func addGroupingPolicies(permission *Permission) error {
func removeGroupingPolicies(permission *Permission) error {
func Enforce(permission *Permission, request []string, permissionIds ...string) (bool, error) {
	// type transformation
func BatchEnforce(permission *Permission, requests [][]string, permissionIds ...string) ([]bool, error) {
	// type transformation
func getEnforcers(userId string) ([]*casbin.Enforcer, error) {
func GetAllObjects(userId string) ([]string, error) {
func GetAllActions(userId string) ([]string, error) {
func GetAllRoles(userId string) ([]string, error) {
func GetBuiltInModel(modelText string) (model.Model, error) {
		// load [policy_definition]
		// filled empty field with "" and V5 with "permissionId"