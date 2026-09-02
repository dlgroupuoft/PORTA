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
func InitFlag() {
	// Load beego config from the specified config path
func ShouldExportData() bool {
func GetExportFilePath() string {
func InitConfig() {
func InitAdapter() {
func CreateTables() {
// Ormer represents the MySQL adapter for policy storage.
type Ormer struct {
// finalizer is the destructor for Ormer.
func finalizer(a *Ormer) {
// NewAdapter is the constructor for Ormer.
func NewAdapter(driverName string, dataSourceName string, dbName string) (*Ormer, error) {
	// Open the DB, create it if not existed.
	// Call the destructor when the object is released.
// NewAdapterFromDb is the constructor for Ormer.
func NewAdapterFromDb(driverName string, dataSourceName string, dbName string, db *sql.DB) (*Ormer, error) {
	// Open the DB, create it if not existed.
	// Call the destructor when the object is released.
func refineDataSourceNameForPostgres(dataSourceName string) string {
func createDatabaseForPostgres(driverName string, dataSourceName string, dbName string) error {
func (a *Ormer) CreateDatabase() error {
func (a *Ormer) open() error {
func (a *Ormer) openFromDb(db *sql.DB) error {
func (a *Ormer) close() {
func (a *Ormer) createTable() {