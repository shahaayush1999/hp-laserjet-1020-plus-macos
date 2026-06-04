/* Function: 100103f8 hp1020_jobmgr_send_case_6_candidate */


void hp1020_jobmgr_send_case_6_candidate(void)

{
  undefined4 local_30 [12];

  local_30[0] = 6;
  hp1020_queue_send_candidate(3,local_30);
  return;
}
