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
// GetCerts
// @Title GetCerts
// @Tag Cert API
// @Description get certs
// @Param   owner     query    string  true        "The owner of certs"
// @Success 200 {array} object.Cert The Response object
// @router /get-certs [get]
func (c *ApiController) GetCerts() {
// GetGlobalCerts
// @Title GetGlobalCerts
// @Tag Cert API
// @Description get global certs
// @Success 200 {array} object.Cert The Response object
// @router /get-global-certs [get]
func (c *ApiController) GetGlobalCerts() {
// GetCert
// @Title GetCert
// @Tag Cert API
// @Description get cert
// @Param   id     query    string  true        "The id ( owner/name ) of the cert"
// @Success 200 {object} object.Cert The Response object
// @router /get-cert [get]
func (c *ApiController) GetCert() {
// UpdateCert
// @Title UpdateCert
// @Tag Cert API
// @Description update cert
// @Param   id     query    string  true        "The id ( owner/name ) of the cert"
// @Param   body    body   object.Cert  true        "The details of the cert"
// @Success 200 {object} controllers.Response The Response object
// @router /update-cert [post]
func (c *ApiController) UpdateCert() {
// AddCert
// @Title AddCert
// @Tag Cert API
// @Description add cert
// @Param   body    body   object.Cert  true        "The details of the cert"
// @Success 200 {object} controllers.Response The Response object
// @router /add-cert [post]
func (c *ApiController) AddCert() {
// DeleteCert
// @Title DeleteCert
// @Tag Cert API
// @Description delete cert
// @Param   body    body   object.Cert  true        "The details of the cert"
// @Success 200 {object} controllers.Response The Response object
// @router /delete-cert [post]
func (c *ApiController) DeleteCert() {
// UpdateCertDomainExpire
// @Title UpdateCertDomainExpire
// @Tag Cert API
// @Description update cert domain expire time
// @Param   id     query   string  true        "The ID of the cert"
// @Success 200 {object} controllers.Response The Response object
// @router /update-cert-domain-expire [post]
func (c *ApiController) UpdateCertDomainExpire() {