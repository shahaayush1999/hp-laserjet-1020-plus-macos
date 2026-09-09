/* Function: 10010170 hp1020_print_mgr_emit_media_status_candidate */


/* print-manager fallout mapping candidate */

void hp1020_print_mgr_emit_media_status_candidate(void)

{
  undefined4 local_50 [2];
  undefined4 uStack_48;
  undefined4 uStack_40;
  undefined4 uStack_3c;
  undefined4 uStack_38;
  undefined4 uStack_34;
  undefined4 uStack_30;
  undefined4 *puStack_2c;

  uStack_30 = 0x1f;
  puStack_2c = &uStack_40;
  hp1020_datastore_read_locked_candidate(&uStack_30);
  uStack_40 = *(undefined4 *)(hp1020_print_mgr_pending_media_ptr_word + 4);
  uStack_3c = *(undefined4 *)hp1020_print_mgr_pending_media_ptr_word;
  uStack_38 = *(undefined4 *)(hp1020_print_mgr_pending_media_ptr_word + 8);
  if (*(int *)(hp1020_print_mgr_pending_media_ptr_word + 0xc) - 1U < 7) {
                    /* WARNING: Could not recover jumptable at 0x100101a9. Too many branches */
                    /* WARNING: Treating indirect jump as call */
    (**(code **)(PTR_switchdataD_10004a00_100063a4 +
                (*(int *)(hp1020_print_mgr_pending_media_ptr_word + 0xc) - 1U) * 4))();
    return;
  }
  uStack_34 = 0;
  hp1020_datastore_write_notify_unlock_candidate(&uStack_30);
  local_50[0] = 0x2c;
  uStack_48 = 1;
  hp1020_queue_send_candidate(10,local_50);
  return;
}
