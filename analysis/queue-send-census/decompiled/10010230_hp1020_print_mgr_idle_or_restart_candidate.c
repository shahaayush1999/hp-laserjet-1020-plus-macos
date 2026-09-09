/* Function: 10010230 hp1020_print_mgr_idle_or_restart_candidate */


void hp1020_print_mgr_idle_or_restart_candidate(int *param_1)

{
  undefined *puVar1;

  if (*param_1 == 0x17) {
    if (hp1020_print_mgr_state_ptr_word[8] != '\0') {
      hp1020_print_mgr_state_ptr_word[8] = hp1020_print_mgr_state_ptr_word[8] + -1;
    }
  }
  else {
    if (*param_1 == 0xb) {
      if ((*hp1020_print_mgr_state_ptr_word == '\0') &&
         (*(int *)(hp1020_print_mgr_state_ptr_word + 0x10) == DAT_100063a8)) {
        hp1020_queue_send_message4_candidate(0,0x4a,0,0);
      }
    }
    puVar1 = hp1020_print_mgr_state_ptr_word;
    if (((hp1020_print_mgr_state_ptr_word[8] == '\0') &&
        (*(int *)(hp1020_print_mgr_state_ptr_word + 0xc) == 0)) &&
       ((*hp1020_print_mgr_state_ptr_word == '\0' || (hp1020_print_mgr_state_ptr_word[2] == '\0'))))
    {
      hp1020_queue_send_message4_candidate(0,0x18,0,0);
      puVar1[8] = puVar1[8] + '\x01';
    }
  }
  return;
}
