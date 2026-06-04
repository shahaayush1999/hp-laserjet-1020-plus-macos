/* Function: 100100a8 hp1020_print_mgr_status_aux_candidate */


/* low confidence: PrintMgr helper used when handling completion/status path */

void hp1020_print_mgr_status_aux_candidate(void)

{
  bool bVar1;
  uint *puVar2;

  puVar2 = (uint *)hp1020_datastore_lock_entry_candidate(0x1d);
  bVar1 = false;
  if ((((*puVar2 & 4) != 0) && (puVar2[0xe] != 0)) && (puVar2[0xd] == 0)) {
    bVar1 = true;
  }
  hp1020_datastore_unlock_entry_candidate(0x1d);
  if (bVar1) {
    hp1020_queue_send_message4_candidate(0,0x1a,0,0);
  }
  return;
}
