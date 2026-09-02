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
// GetSyncers
// @Title GetSyncers
// @Tag Syncer API
// @Description get syncers
// @Param   owner     query    string  true        "The owner of syncers"
// @Success 200 {array} object.Syncer The Response object
// @router /get-syncers [get]
func (c *ApiController) GetSyncers() {
// GetSyncer
// @Title GetSyncer
// @Tag Syncer API
// @Description get syncer
// @Param   id     query    string  true        "The id ( owner/name ) of the syncer"
// @Success 200 {object} object.Syncer The Response object
// @router /get-syncer [get]
func (c *ApiController) GetSyncer() {
// UpdateSyncer
// @Title UpdateSyncer
// @Tag Syncer API
// @Description update syncer
// @Param   id     query    string  true        "The id ( owner/name ) of the syncer"
// @Param   body    body   object.Syncer  true        "The details of the syncer"
// @Success 200 {object} controllers.Response The Response object
// @router /update-syncer [post]
func (c *ApiController) UpdateSyncer() {
// AddSyncer
// @Title AddSyncer
// @Tag Syncer API
// @Description add syncer
// @Param   body    body   object.Syncer  true        "The details of the syncer"
// @Success 200 {object} controllers.Response The Response object
// @router /add-syncer [post]
func (c *ApiController) AddSyncer() {
// DeleteSyncer
// @Title DeleteSyncer
// @Tag Syncer API
// @Description delete syncer
// @Param   body    body   object.Syncer  true        "The details of the syncer"
// @Success 200 {object} controllers.Response The Response object
// @router /delete-syncer [post]
func (c *ApiController) DeleteSyncer() {
// RunSyncer
// @Title RunSyncer
// @Tag Syncer API
// @Description run syncer
// @Param   body    body   object.Syncer  true        "The details of the syncer"
// @Success 200 {object} controllers.Response The Response object
// @router /run-syncer [get]
func (c *ApiController) RunSyncer() {
func (c *ApiController) TestSyncerDb() {