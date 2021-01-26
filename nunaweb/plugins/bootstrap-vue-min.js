import Vue from 'vue';

import { SpinnerPlugin } from 'bootstrap-vue/esm/components/spinner';
import { BIcon, BIconCheckCircleFill, BIconExclamationCircleFill } from 'bootstrap-vue';

Vue.use(SpinnerPlugin);
Vue.component('BIcon', BIcon);
Vue.component('BIconCheckCircleFill', BIconCheckCircleFill);
Vue.component('BIconExclamationCircleFill', BIconExclamationCircleFill);
