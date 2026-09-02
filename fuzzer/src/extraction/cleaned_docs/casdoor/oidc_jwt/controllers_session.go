// Copyright 2022 The Casdoor Authors. All Rights Reserved.
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
// GetSessions
// @Title GetSessions
// @Tag Session API
// @Description Get organization user sessions.
// @Param   owner     query    string  true        "The organization name"
// @Success 200 {array} string The Response object
// @router /get-sessions [get]
func (c *ApiController) GetSessions() {
// GetSingleSession
// @Title GetSingleSession
// @Tag Session API
// @Description Get session for one user in one application.
// @Param   sessionPkId     query    string  true        "The session ID in format: organization/user/application (e.g., built-in/admin/app-built-in)"
// @Success 200 {array} string The Response object
// @router /get-session [get]
func (c *ApiController) GetSingleSession() {
// UpdateSession
// @Title UpdateSession
// @Tag Session API
// @Description Update session for one user in one application.
// @Param   body     body    object.Session  true        "The session object to update"
// @Success 200 {object} controllers.Response The Response object
// @router /update-session [post]
func (c *ApiController) UpdateSession() {
// AddSession
// @Title AddSession
// @Tag Session API
// @Description Add session for one user in one application. If there are other existing sessions, join the session into the list.
// @Param   body     body    object.Session  true        "The session object to add"
// @Success 200 {object} controllers.Response The Response object
// @router /add-session [post]
func (c *ApiController) AddSession() {
// DeleteSession
// @Title DeleteSession
// @Tag Session API
// @Description Delete session for one user in one application.
// @Param   body     body    object.Session  true        "The session object to delete"
// @Success 200 {object} controllers.Response The Response object
// @router /delete-session [post]
func (c *ApiController) DeleteSession() {
// IsSessionDuplicated
// @Title IsSessionDuplicated
// @Tag Session API
// @Description Check if there are other different sessions for one user in one application.
// @Param   sessionPkId     query    string  true        "The session ID in format: organization/user/application (e.g., built-in/admin/app-built-in)"
// @Param   sessionId     query    string  true        "The specific session ID to check"
// @Success 200 {array} string The Response object
// @router /is-session-duplicated [get]
func (c *ApiController) IsSessionDuplicated() {