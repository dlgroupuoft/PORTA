// Copyright 2023 The casbin Authors. All Rights Reserved.
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
type NodeItem struct {
type Site struct {
func GetGlobalSites() ([]*Site, error) {
func GetSites(owner string) ([]*Site, error) {
func getSite(owner string, name string) (*Site, error) {
func GetSite(id string) (*Site, error) {
func GetMaskedSite(site *Site, node string) *Site {
func GetMaskedSites(sites []*Site, node string) []*Site {
func UpdateSite(id string, site *Site) (bool, error) {
func UpdateSiteNoRefresh(id string, site *Site) (bool, error) {
func AddSite(site *Site) (bool, error) {
func DeleteSite(site *Site) (bool, error) {
func (site *Site) GetId() string {
func (site *Site) GetChallengeMap() map[string]string {
func (site *Site) GetHost() string {
func addErrorToMsg(msg string, function string, err error) string {
func GetSiteCount(owner, field, value string) (int64, error) {
func GetPaginationSites(owner string, offset, limit int, field, value, sortField, sortOrder string) ([]*Site, error) {