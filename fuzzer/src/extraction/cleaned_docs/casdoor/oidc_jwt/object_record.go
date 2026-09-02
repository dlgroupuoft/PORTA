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
func init() {
type Record struct {
type Response struct {
func maskPassword(recordString string) string {
func NewRecord(ctx *context.Context) (*casvisorsdk.Record, error) {
func addRecord(record *casvisorsdk.Record) (int64, error) {
func AddRecord(record *casvisorsdk.Record) bool {
func GetRecordCount(field, value string, filterRecord *casvisorsdk.Record) (int64, error) {
func GetRecords() ([]*casvisorsdk.Record, error) {
func GetPaginationRecords(offset, limit int, field, value, sortField, sortOrder string, filterRecord *casvisorsdk.Record) ([]*casvisorsdk.Record, error) {
func GetRecordsByField(record *casvisorsdk.Record) ([]*casvisorsdk.Record, error) {
func CopyRecord(record *casvisorsdk.Record) *casvisorsdk.Record {
func getFilteredWebhooks(webhooks []*Webhook, organization string, action string) []*Webhook {
func addWebhookRecord(webhook *Webhook, record *casvisorsdk.Record, statusCode int, respBody string, sendError error) error {
func filterRecordObject(object string, objectFields []string) string {
func SendWebhooks(record *casvisorsdk.Record) error {