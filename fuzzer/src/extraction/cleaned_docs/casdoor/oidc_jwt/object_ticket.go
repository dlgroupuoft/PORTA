// Copyright 2024 The Casdoor Authors. All Rights Reserved.
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
type TicketMessage struct {
type Ticket struct {
func GetTicketCount(owner, field, value string) (int64, error) {
func GetTickets(owner string) ([]*Ticket, error) {
func GetPaginationTickets(owner string, offset, limit int, field, value, sortField, sortOrder string) ([]*Ticket, error) {
func GetUserTickets(owner, user string) ([]*Ticket, error) {
func getTicket(owner string, name string) (*Ticket, error) {
func GetTicket(id string) (*Ticket, error) {
func UpdateTicket(id string, ticket *Ticket) (bool, error) {
func AddTicket(ticket *Ticket) (bool, error) {
func DeleteTicket(ticket *Ticket) (bool, error) {
func (ticket *Ticket) GetId() string {
func AddTicketMessage(id string, message *TicketMessage) (bool, error) {