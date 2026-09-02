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
type Model struct {
func GetModelCount(owner, field, value string) (int64, error) {
func GetModels(owner string) ([]*Model, error) {
func GetPaginationModels(owner string, offset, limit int, field, value, sortField, sortOrder string) ([]*Model, error) {
func getModel(owner string, name string) (*Model, error) {
func GetModel(id string) (*Model, error) {
func getModelEx(id string) (*Model, error) {
func UpdateModelWithCheck(id string, modelObj *Model) error {
	// check model grammar
func UpdateModel(id string, modelObj *Model) (bool, error) {
func AddModel(model *Model) (bool, error) {
func DeleteModel(model *Model) (bool, error) {
func (m *Model) GetId() string {
func modelChangeTrigger(oldName string, newName string) error {
func HasRoleDefinition(m model.Model) bool {
func (m *Model) initModel() error {
func getModelCfg(m *Model) (map[string]string, error) {