/* Function: 10010158 hp1020_print_mgr_clear_pending_media_candidate */


/* print-manager fallout mapping candidate */

void hp1020_print_mgr_clear_pending_media_candidate(void)

{
  undefined *puVar1;

  puVar1 = hp1020_print_mgr_pending_media_ptr_word;
  if (*(int *)(hp1020_print_mgr_pending_media_ptr_word + 0xc) != 0) {
    *(undefined4 *)(hp1020_print_mgr_pending_media_ptr_word + 0xc) = 0;
    *(undefined4 *)(puVar1 + 8) = 4;
    *(undefined4 *)(puVar1 + 4) = 0;
    *(undefined4 *)puVar1 = 0;
  }
  return;
}
