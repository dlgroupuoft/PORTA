package object
type LdapAutoSynchronizer struct {
func InitLdapAutoSynchronizer() {
func NewLdapAutoSynchronizer() *LdapAutoSynchronizer {
func GetLdapAutoSynchronizer() *LdapAutoSynchronizer {
// StartAutoSync
// start autosync for specified ldap, old existing autosync goroutine will be ceased
func (l *LdapAutoSynchronizer) StartAutoSync(ldapId string) error {
func (l *LdapAutoSynchronizer) StopAutoSync(ldapId string) {
// autosync goroutine
func (l *LdapAutoSynchronizer) syncRoutine(ldap *Ldap, stopChan chan struct{}) error {
		// fetch all users and groups
		// Sync groups first if enabled (so they exist before assigning users)
// LdapAutoSynchronizerStartUpAll
// start all autosync goroutine for existing ldap servers in each organizations
func (l *LdapAutoSynchronizer) LdapAutoSynchronizerStartUpAll() error {
func UpdateLdapSyncTime(ldapId string) error {