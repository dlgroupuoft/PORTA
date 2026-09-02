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
type AccountItem struct {
type ThemeData struct {
type MfaItem struct {
type Organization struct {
func GetOrganizationCount(owner, name, field, value string) (int64, error) {
func GetOrganizations(owner string, name ...string) ([]*Organization, error) {
func GetOrganizationsByFields(owner string, fields ...string) ([]*Organization, error) {
func GetPaginationOrganizations(owner string, name string, offset, limit int, field, value, sortField, sortOrder string) ([]*Organization, error) {
func getOrganization(owner string, name string) (*Organization, error) {
func GetOrganization(id string) (*Organization, error) {
func GetMaskedOrganization(organization *Organization, errs ...error) (*Organization, error) {
func GetMaskedOrganizations(organizations []*Organization, errs ...error) ([]*Organization, error) {
func UpdateOrganization(id string, organization *Organization, isGlobalAdmin bool) (bool, error) {
func AddOrganization(organization *Organization) (bool, error) {
func deleteOrganization(organization *Organization) (bool, error) {
func DeleteOrganization(organization *Organization) (bool, error) {
func GetOrganizationByUser(user *User) (*Organization, error) {
func GetAccountItemByName(name string, organization *Organization) *AccountItem {
func CheckAccountItemModifyRule(accountItem *AccountItem, isAdmin bool, lang string) (bool, string) {
func GetDefaultApplication(id string) (*Application, error) {
func organizationChangeTrigger(oldName string, newName string) error {
		// u = organization/username
		// u = organization/username
		// u = organization/username
		// u = organization/username
func IsNeedPromptMfa(org *Organization, user *User) bool {
func (org *Organization) GetInitScore() (int, error) {
func UpdateOrganizationBalance(owner string, name string, balance float64, currency string, isOrgBalance bool, lang string) error {
	// Convert the balance amount from transaction currency to organization's balance currency
		// Check organization balance credit limit
		// User balance is just a sum of all users' balances, no credit limit check here
		// Individual user credit limits are checked in UpdateUserBalance