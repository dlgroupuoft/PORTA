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
package controllers
// ResponseJsonData ...
func (c *ApiController) ResponseJsonData(resp *Response, data ...interface{}) {
// ResponseOk ...
func (c *ApiController) ResponseOk(data ...interface{}) {
// ResponseError ...
func (c *ApiController) ResponseError(error string, data ...interface{}) {
func (c *ApiController) T(error string) string {
// GetAcceptLanguage ...
func (c *ApiController) GetAcceptLanguage() string {
// SetTokenErrorHttpStatus ...
func (c *ApiController) SetTokenErrorHttpStatus() {
// RequireSignedIn ...
func (c *ApiController) RequireSignedIn() (string, bool) {
// RequireSignedInUser ...
func (c *ApiController) RequireSignedInUser() (*object.User, bool) {
// RequireAdmin ...
func (c *ApiController) RequireAdmin() (string, bool) {
func (c *ApiController) IsOrgAdmin() (bool, bool) {
// IsMaskedEnabled ...
func (c *ApiController) IsMaskedEnabled() (bool, bool) {
func refineFullFilePath(fullFilePath string) (string, string) {
func (c *ApiController) GetProviderFromContext(category string) (*object.Provider, error) {
func checkQuotaForApplication(count int) error {
func checkQuotaForOrganization(count int) error {
func checkQuotaForProvider(count int) error {
func checkQuotaForUser() error {
func getInvalidSmsReceivers(smsForm SmsForm) []string {
		// The receiver phone format: E164 like +8613854673829 +441932567890