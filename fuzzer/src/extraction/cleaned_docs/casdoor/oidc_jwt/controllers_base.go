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
// ApiController
// controller for handlers under /api uri
type ApiController struct {
// RootController
// controller for handlers directly under / (root)
type RootController struct {
type SessionData struct {
func (c *ApiController) IsGlobalAdmin() bool {
func (c *ApiController) IsAdmin() bool {
func (c *ApiController) IsAdminOrSelf(user2 *object.User) bool {
func (c *ApiController) isGlobalAdmin() (bool, *object.User) {
		// e.g., "app/app-casnode"
func (c *ApiController) getCurrentUser() *object.User {
// GetSessionUsername ...
func (c *ApiController) GetSessionUsername() string {
	// prefer username stored in Beego context by ApiFilter
	// check if user session expired
// GetPaidUsername ...
func (c *ApiController) GetPaidUsername() string {
	// check if user session expired
func (c *ApiController) GetSessionToken() string {
func (c *ApiController) GetSessionApplication() *object.Application {
func (c *ApiController) ClearUserSession() {
func (c *ApiController) ClearTokenSession() {
func (c *ApiController) GetSessionOidc() (string, string) {
// SetSessionUsername ...
func (c *ApiController) SetSessionUsername(user string) {
func (c *ApiController) SetSessionToken(accessToken string) {
// GetSessionData ...
func (c *ApiController) GetSessionData() *SessionData {
// SetSessionData ...
func (c *ApiController) SetSessionData(s *SessionData) {
func (c *ApiController) setMfaUserSession(userId string) {
func (c *ApiController) getMfaUserSession() string {
func (c *ApiController) setExpireForSession(cookieExpireInHours int64) {
func wrapActionResponse(affected bool, e ...error) *Response {
func wrapErrorResponse(err error) *Response {
func (c *ApiController) Finish() {