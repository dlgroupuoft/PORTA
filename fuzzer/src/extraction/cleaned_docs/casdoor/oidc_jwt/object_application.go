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
type SigninMethod struct {
type SignupItem struct {
type SigninItem struct {
type SamlItem struct {
type JwtItem struct {
type ScopeItem struct {
type Application struct {
	// Reverse proxy fields
func GetApplicationCount(owner, field, value string) (int64, error) {
func GetOrganizationApplicationCount(owner, organization, field, value string) (int64, error) {
func GetApplications(owner string) ([]*Application, error) {
func GetOrganizationApplications(owner string, organization string) ([]*Application, error) {
func GetPaginationApplications(owner string, offset, limit int, field, value, sortField, sortOrder string) ([]*Application, error) {
func GetPaginationOrganizationApplications(owner, organization string, offset, limit int, field, value, sortField, sortOrder string) ([]*Application, error) {
func getProviderMap(owner string) (m map[string]*Provider, err error) {
func extendApplicationWithProviders(application *Application) (err error) {
func extendApplicationWithOrg(application *Application) (err error) {
func extendApplicationWithSigninItems(application *Application) (err error) {
func extendApplicationWithSigninMethods(application *Application) (err error) {
func extendApplicationWithSignupItems(application *Application) (err error) {
func getApplication(owner string, name string) (*Application, error) {
func GetApplicationByOrganizationName(organization string) (*Application, error) {
func GetApplicationByUser(user *User) (*Application, error) {
func GetApplicationByUserId(userId string) (application *Application, err error) {
func GetApplicationByClientId(clientId string) (*Application, error) {
func GetApplication(id string) (*Application, error) {
func GetMaskedApplication(application *Application, userId string) *Application {
func GetMaskedApplications(applications []*Application, userId string) []*Application {
func GetAllowedApplications(applications []*Application, userId string, lang string) ([]*Application, error) {
func checkMultipleCaptchaProviders(application *Application, lang string) error {
func UpdateApplication(id string, application *Application, isGlobalAdmin bool, lang string) (bool, error) {
func AddApplication(application *Application) (bool, error) {
	// Initialize default values for required fields to prevent UI errors
func deleteApplication(application *Application) (bool, error) {
func DeleteApplication(application *Application) (bool, error) {
func (application *Application) GetId() string {
func (application *Application) IsRedirectUriValid(redirectUri string) bool {
func (application *Application) IsPasswordEnabled() bool {
func (application *Application) IsPasswordWithLdapEnabled() bool {
func (application *Application) IsCodeSigninViaEmailEnabled() bool {
func (application *Application) IsCodeSigninViaSmsEnabled() bool {
func (application *Application) IsLdapEnabled() bool {
func (application *Application) IsFaceIdEnabled() bool {
func IsOriginAllowed(origin string) (bool, error) {
func getApplicationMap(organization string) (map[string]*Application, error) {
func ExtendManagedAccountsWithUser(user *User) (*User, error) {
func applicationChangeTrigger(oldName string, newName string) error {