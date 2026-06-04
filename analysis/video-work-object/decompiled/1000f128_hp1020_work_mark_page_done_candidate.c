/* Function: 1000f128 hp1020_work_mark_page_done_candidate */


void hp1020_work_mark_page_done_candidate(int param_1)

{
  undefined2 uVar1;

  *(short *)(param_1 + 0x4e) = *(short *)(param_1 + 0x4e) + -1;
  if (*(short *)(param_1 + 0x72) == 1) {
    uVar1 = 1;
  }
  else {
    if (*(char *)(param_1 + 0x75) == '\x01') {
      hp1020_work_list_mark_or_send_candidate(param_1 + 0x50,2);
      *(short *)(param_1 + 0x4e) = *(short *)(param_1 + 0x4e) + -1;
    }
    uVar1 = 0;
  }
  hp1020_work_list_mark_or_send_candidate(param_1 + 0x50,uVar1);
  return;
}
