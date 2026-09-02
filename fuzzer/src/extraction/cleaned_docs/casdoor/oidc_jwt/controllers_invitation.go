// Copyright 2023 The Casdoor Authors. All Rights Reserved.
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
// GetInvitations
// @Title GetInvitations
// @Tag Invitation API
// @Description get invitations
// @Param   owner     query    string  true        "The owner of invitations"
// @Success 200 {array} object.Invitation The Response object
// @router /get-invitations [get]
func (c *ApiController) GetInvitations() {
// GetInvitation
// @Title GetInvitation
// @Tag Invitation API
// @Description get invitation
// @Param   id     query    string  true        "The id ( owner/name ) of the invitation"
// @Success 200 {object} object.Invitation The Response object
// @router /get-invitation [get]
func (c *ApiController) GetInvitation() {
// GetInvitationCodeInfo
// @Title GetInvitationCodeInfo
// @Tag Invitation API
// @Description get invitation code information
// @Param   code     query    string  true        "Invitation code"
// @Success 200 {object} object.Invitation The Response object
// @router /get-invitation-info [get]
func (c *ApiController) GetInvitationCodeInfo() {
// UpdateInvitation
// @Title UpdateInvitation
// @Tag Invitation API
// @Description update invitation
// @Param   id     query    string  true        "The id ( owner/name ) of the invitation"
// @Param   body    body   object.Invitation  true        "The details of the invitation"
// @Success 200 {object} controllers.Response The Response object
// @router /update-invitation [post]
func (c *ApiController) UpdateInvitation() {
// AddInvitation
// @Title AddInvitation
// @Tag Invitation API
// @Description add invitation
// @Param   body    body   object.Invitation  true        "The details of the invitation"
// @Success 200 {object} controllers.Response The Response object
// @router /add-invitation [post]
func (c *ApiController) AddInvitation() {
// DeleteInvitation
// @Title DeleteInvitation
// @Tag Invitation API
// @Description delete invitation
// @Param   body    body   object.Invitation  true        "The details of the invitation"
// @Success 200 {object} controllers.Response The Response object
// @router /delete-invitation [post]
func (c *ApiController) DeleteInvitation() {
// VerifyInvitation
// @Title VerifyInvitation
// @Tag Invitation API
// @Description verify invitation
// @Param   id     query    string  true        "The id ( owner/name ) of the invitation"
// @Success 200 {object} controllers.Response The Response object
// @router /verify-invitation [get]
func (c *ApiController) VerifyInvitation() {
// SendInvitation
// @Title VerifyInvitation
// @Tag Invitation API
// @Description verify invitation
// @Param   id     query    string	true        "The id ( owner/name ) of the invitation"
// @Param   body    body	[]string  true        "The details of the invitation"
// @Success 200 {object} controllers.Response The Response object
// @router /send-invitation [post]
func (c *ApiController) SendInvitation() {