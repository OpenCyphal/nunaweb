import Vue from 'vue';
import Router from 'vue-router';

import Index from './pages/index.vue';

Vue.use(Router);

export function createRouter() {
  return new Router({
    routes: [
      {
        name: 'index',
        path: '/',
        component: Index
      },
      {
        name: 'status',
        path: '/status/:statusID',
        component: Index
      }
    ]
  });
}
