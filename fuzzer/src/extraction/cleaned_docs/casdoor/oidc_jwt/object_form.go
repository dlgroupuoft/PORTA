// Copyright 2025 The Casdoor Authors. All Rights Reserved.
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
type FormItem struct {
type Form struct {
func GetMaskedForm(form *Form, isMaskEnabled bool) *Form {
func GetMaskedForms(forms []*Form, isMaskEnabled bool) []*Form {
func GetGlobalForms() ([]*Form, error) {
func GetForms(owner string) ([]*Form, error) {
func getForm(owner string, name string) (*Form, error) {
func GetForm(id string) (*Form, error) {
func UpdateForm(id string, form *Form) (bool, error) {
func AddForm(form *Form) (bool, error) {
func DeleteForm(form *Form) (bool, error) {
func (form *Form) GetId() string {
func GetFormCount(owner string, field, value string) (int64, error) {
func GetPaginationForms(owner string, offset, limit int, field, value, sortField, sortOrder string) ([]*Form, error) {