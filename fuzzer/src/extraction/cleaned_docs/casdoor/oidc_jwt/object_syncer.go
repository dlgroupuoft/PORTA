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
type TableColumn struct {
type Syncer struct {
func GetSyncerCount(owner, organization, field, value string) (int64, error) {
func GetSyncers(owner string) ([]*Syncer, error) {
func GetOrganizationSyncers(owner, organization string) ([]*Syncer, error) {
func GetPaginationSyncers(owner, organization string, offset, limit int, field, value, sortField, sortOrder string) ([]*Syncer, error) {
func getSyncer(owner string, name string) (*Syncer, error) {
func GetSyncer(id string) (*Syncer, error) {
func GetMaskedSyncer(syncer *Syncer, errs ...error) (*Syncer, error) {
func GetMaskedSyncers(syncers []*Syncer, errs ...error) ([]*Syncer, error) {
func UpdateSyncer(id string, syncer *Syncer, isGlobalAdmin bool, lang string) (bool, error) {
	// Close old syncer connections before updating
func updateSyncerErrorText(syncer *Syncer, line string) (bool, error) {
func AddSyncer(syncer *Syncer) (bool, error) {
func DeleteSyncer(syncer *Syncer) (bool, error) {
func (syncer *Syncer) GetId() string {
func (syncer *Syncer) getTableColumnsTypeMap() map[string]string {
func (syncer *Syncer) getTable() string {
func (syncer *Syncer) getKeyColumn() *TableColumn {
func (syncer *Syncer) getLocalPrimaryKey() string {
func (syncer *Syncer) getTargetTablePrimaryKey() string {
func RunSyncer(syncer *Syncer) error {
func TestSyncer(syncer Syncer) error {
func (syncer *Syncer) Close() error {