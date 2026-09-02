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
type Cert struct {
func GetMaskedCert(cert *Cert) *Cert {
func GetMaskedCerts(certs []*Cert, err error) ([]*Cert, error) {
func GetCertCount(owner, field, value string) (int64, error) {
func GetCerts(owner string) ([]*Cert, error) {
func GetPaginationCerts(owner string, offset, limit int, field, value, sortField, sortOrder string) ([]*Cert, error) {
func GetGlobalCertsCount(field, value string) (int64, error) {
func GetGlobalCerts() ([]*Cert, error) {
func GetPaginationGlobalCerts(offset, limit int, field, value, sortField, sortOrder string) ([]*Cert, error) {
func getCert(owner string, name string) (*Cert, error) {
func getCertByName(name string) (*Cert, error) {
func GetCert(id string) (*Cert, error) {
func UpdateCert(id string, cert *Cert) (bool, error) {
func AddCert(cert *Cert) (bool, error) {
func DeleteCert(cert *Cert) (bool, error) {
func (p *Cert) GetId() string {
func (p *Cert) populateContent() error {
func RenewCert(cert *Cert) (bool, error) {
func getCertByApplication(application *Application) (*Cert, error) {
func GetDefaultCert() (*Cert, error) {
func certChangeTrigger(oldName string, newName string) error {
func getBaseDomain(domain string) (string, error) {
	// abc.com -> abc.com
	// abc.com.it -> abc.com.it
	// subdomain.abc.io -> abc.io
	// subdomain.abc.org.us -> abc.org.us
func GetCertByDomain(domain string) (*Cert, error) {
func getCertMap() (map[string]*Cert, error) {
func (p *Cert) isCertNearExpire() (bool, error) {