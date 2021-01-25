<!-- TODO: Break this thing up! It's massive. -->
<template>
  <div class="container d-flex flex-column align-items-center text-center pt-5 px-5">
    <form style="max-width: 960px" v-on:submit="handleSubmit" enctype="multipart/form-data">
      <Logo style="margin-bottom: 3rem" />
      <h1 class="title">
        nunaweb
      </h1>
      <h2 class="lead">
        transpile DSDL code from the web
      </h2>
      <ArchiveSelector
        id="0"
        :disabled="taskInProgress"
        v-on:repo-change="handleRepoChange"
        class="mt-3 mb-1"
      />
      <div style="position: relative; text-align: left">
        <ArchiveSelector
          v-for="n in nsFilesKeys"
          :key="n"
          :id="n"
          :initialValue="nsFiles[n]"
          :disabled="taskInProgress"
          v-on:repo-change="handleRepoChange"
          v-on:repo-remove="handleRepoRemove"
          class="my-1"
          removable
        />
        <a
          href="#"
          class="mt-1 me-auto"
          v-bind:class="{ 'disabled': taskInProgress }"
          type="button"
          style="text-decoration: none"
        >
          + Add Namespaces
        </a>
      </div>
      <div class="d-flex mt-4">
        <select
          :disabled="taskInProgress"
          v-model="selectedLang"
          class="form-select me-2"
          aria-label="Target Language"
        >
          <option
            v-for="lang in languages"
            :key="lang.value"
            :disabled="lang.disabled"
            :value="lang.value"
          >
          {{ lang.name }}
          </option>
        </select>
        <select
          :disabled="taskInProgress"
          v-model="selectedEndian"
          class="form-select"
          aria-label="Select Endianness"
        >
          <option
            v-for="endian in endians"
            :key="endian.value"
            :value="endian.value"
          >
          {{ endian.name }}
          </option>
        </select>
      </div>
      <div class="align-items-start mt-3" style="text-align: left !important">
        <div v-for="flag in flags" :key="flag.flag" class="form-check">
          <input
            :disabled="taskInProgress"
            class="form-check-input"
            type="checkbox"
            v-model="flag.value"
            :id="flag.flag"
            />
          <label class="form-check-label" :for="flag.flag">
            {{ flag.name }}
            <code>{{ flag.flag }}</code>
          </label>
          <p class="small" v-if="flag.description">
            {{ flag.description }}
          </p>
        </div>
        <p class="mt-2 mb-0" v-if="command">Generation command:</p>
        <pre style="white-space: pre-wrap" v-if="command">{{ command }}</pre>
        <div class="d-flex align-items-center mt-4 flex-wrap">
          <button
            v-if="taskInProgress"
            type="button"
            v-on:click="handleCancel"
            class="btn btn-secondary me-3 mb-4"
          >
            Cancel
          </button>
          <input
            v-else
            type="submit"
            class="btn btn-primary me-3 mb-4"
            value="Submit"
          />
          <div
            class="d-flex flex-nowrap align-items-center mb-4"
            v-if="loadingStatus !== ''"
          >
            <b-icon
              v-if="loadingStatus === 'SUCCESS'"
              icon="check-circle-fill"
              variant="success"
              style="width: 2rem; height: 2rem;"
              class="me-2"
            />
            <b-icon
              v-else-if="loadingStatus === 'FAILURE' || loadingStatus === 'CANCELED'"
              variant="danger"
              icon="exclamation-circle-fill"
              style="width: 2rem; height: 2rem;"
              class="me-2"
            />
            <b-spinner
              v-else
              style="width: 2rem; height: 2rem;"
              variant="success"
              class="me-2"
            />
            <div class="flex-column">
              <label v-if="loadingStatus === 'FAILURE'">
                Generation failed.
              </label>
              <label v-else>
                {{ loadingMessage }}
              </label>
              <p class="small mb-0" v-if="loadingStatus === 'SUCCESS'">
              Download here: <a :href="resultURL">{{ resultURL }}</a>
              </p>
              <p class="small mb-0" v-else-if="loadingStatus === 'FAILURE'">
                {{ loadingMessage }}
              </p>
              <p class="small mb-0" v-else-if="loadingStatus === 'CANCELED'">
              Generation was canceled. You can submit another.
              <a href="#" v-on:click="loadingStatus = ''">Hide</a>
              </p>
              <p v-else class="small mb-0">
                This process can take up to several minutes. Leave the page open!
              </p>
            </div>
          </div>
        </div>
      </div>
    </form>
  </div>
</template>

<script>
import * as dataOptions from '~/services/dataOptions.js';
import * as api from '~/services/api.js';
import { handleErrors } from '~/services/errors.js';

export default {
  data() {
    return {
      loadingStatus: '',
      loadingMessage: '',
      resultURL: '',
      additionalReposOpen: false,
      command: '',
      loadingTimeout: null,
      nsFiles: {
        '0': null,
        '1': 'https://github.com/UAVCAN/public_regulated_data_types'
      },
      currentNSFilesLen: 3,
      selectedLang: 'c',
      selectedEndian: 'little',
      endians: dataOptions.endians,
      flags: dataOptions.flags,
      languages: dataOptions.languages
    }
  },

  computed: {
    nsFilesKeys() {
      return Object.keys(this.nsFiles).filter(key => key !== '0');
    },

    taskInProgress() {
      return [
        'PROGRESS',
        'PENDING',
        'STARTED',
        'RETRY'
      ].includes(this.loadingStatus);
    }
  },

  mounted() {
    // Kick off status callback
    // For when the user returns to a route
    if (this.$route.query.statusID) {
      clearInterval(this.loadingTimeout);
      this.loadingTimeout = setInterval(this.handleProcessing, 500);
    }
  },

  methods: {
    handleRepoChange(id, repo) {
      this.nsFiles = Object.assign({}, this.nsFiles, {
        [id]: repo
      });
    },

    handleRepoAdd() {
      this.nsFiles = Object.assign({}, this.nsFiles, {
        [this.currentNSFilesLen]: null
      });
    },

    handleRepoRemove(id) {
      const files = { ...this.nsFiles };
      delete files[id];

      this.nsFiles = {
        ...files
      };

      this.currentNSFilesLen++;
    },

    async handleSubmit(event) {
      event.preventDefault();
      event.stopPropagation();

      // Append data
      const formData = api.createUploadFormData(
        Object.values(this.nsFiles),
        this.selectedLang,
        this.selectedEndian,
        this.flags
      );

      this.loadingStatus = 'PENDING';
      this.loadingMessage = 'Uploading...';

      try {
        const data = await api.upload(formData);
        console.log(data);

        this.command = data.command;
        const loadingID = data.task_url.split('/')[2];
        // Push query param so that it's stored in user history
        this.$router.push({
          path: this.$route.path,
          query: { statusID: loadingID }
        });

        // Kick off status callback
        this.loadingTimeout = setInterval(this.handleProcessing, 500);
      } catch (e) {
        handleErrors.bind(this)(e);
      }
    },
    async handleProcessing() {
      try {
        const data = await api.getStatus(this.$route.query.statusID);
        this.loadingStatus = data.state;
        this.loadingMessage = data.status;

        if (data.state === 'SUCCESS') {
          this.resultURL = data.result;
          clearInterval(this.loadingTimeout);
        } else if (data.state === 'FAILURE') {
          clearInterval(this.loadingTimeout);
        } else if (data.state === 'CANCELED') {
          clearInterval(this.loadingTimeout);
        }
      } catch (e) {
        handleErrors.bind(this)(e);
      }
    },
    async handleCancel() {
      try {
        await api.cancel(this.$route.query.statusID);
        this.loadingStatus = 'CANCELED';
        this.loadingMessage = 'Task was canceled.';
        this.resultURL = '';
        clearInterval(this.loadingTimeout);
      } catch (e) {
        handleErrors.bind(this)(e);
      }
    }
  }
}
</script>

<style>
pre {
  background-color: #EEE;
  padding: 1rem;
}

a.disabled {
  /* Make the disabled links grayish*/
  color: gray;
  /* And disable the pointer events */
  pointer-events: none;
}
</style>
