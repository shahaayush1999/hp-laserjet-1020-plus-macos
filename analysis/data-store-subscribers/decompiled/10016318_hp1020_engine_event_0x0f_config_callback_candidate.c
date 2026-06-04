/* Function: 10016318 hp1020_engine_event_0x0f_config_callback_candidate */


/* data-store subscriber mapping candidate */

void hp1020_engine_event_0x0f_config_callback_candidate(int param_1,undefined4 param_2)

{
  undefined1 uVar1;

  if (param_1 == 0xf) {
    switch(param_2) {
    case 1:
      uVar1 = 0;
      break;
    case 2:
      uVar1 = 0x10;
      break;
    case 3:
      uVar1 = 0x20;
      break;
    case 4:
      uVar1 = 0x30;
      break;
    case 5:
      uVar1 = 0x3f;
      break;
    default:
      goto switchD_1001632d_default;
    }
    PTR_DAT_10006920[0x59] = uVar1;
  }
switchD_1001632d_default:
  return;
}
