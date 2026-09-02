package object
// https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/sec_usr_radatt/configuration/xe-16/sec-usr-radatt-xe-16-book/sec-rad-ov-ietf-attr.html
type RadiusAccounting struct {
func (ra *RadiusAccounting) GetId() string {
func getRadiusAccounting(owner, name string) (*RadiusAccounting, error) {
func getPaginationRadiusAccounting(owner, field, value, sortField, sortOrder string, offset, limit int) ([]*RadiusAccounting, error) {
func GetRadiusAccounting(id string) (*RadiusAccounting, error) {
func GetRadiusAccountingBySessionId(sessionId string) (*RadiusAccounting, error) {
func AddRadiusAccounting(ra *RadiusAccounting) error {
func DeleteRadiusAccounting(ra *RadiusAccounting) error {
func UpdateRadiusAccounting(id string, ra *RadiusAccounting) error {
func InterimUpdateRadiusAccounting(oldRa *RadiusAccounting, newRa *RadiusAccounting, stop bool) error {