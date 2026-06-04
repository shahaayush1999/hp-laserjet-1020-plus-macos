/* Function: 1001040c hp1020_jobmgr_send_case_2_candidate */


void hp1020_jobmgr_send_case_2_candidate(void)

{
  undefined4 local_30 [12];

  local_30[0] = 2;
  hp1020_queue_send_candidate(3,local_30);
  return;
}
