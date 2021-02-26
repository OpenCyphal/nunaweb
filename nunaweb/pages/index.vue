<!-- TODO: Break this thing up! It's massive. -->
<template>
  <div>
    <div class="container d-flex flex-column align-items-center text-center pt-5 px-5">
      <form style="max-width: 960px" enctype="multipart/form-data" @submit="handleSubmit">
        <Logo style="margin-bottom: 3rem" />
        <h1 class="title">
          nunaweb
        </h1>
        <h2 class="lead">
          transpile DSDL code from the web
        </h2>
        <div class="d-flex justify-content-center">
          <a class="noline mx-3 mb-0" href="https://github.com/UAVCAN/nunaweb">Source</a>
          <a class="noline mx-3 mb-0" href="https://nunavut.readthedocs.io/en/latest/README.html">Nunavut Docs</a>
          <a class="noline mx-3 mb-0" href="https://uavcan.org">UAVCAN</a>
        </div>
        <ArchiveSelector
          id="0"
          class="mt-3 mb-1"
          :disabled="taskInProgress"
          @repo-change="handleRepoChange"
        />
        <div style="position: relative; text-align: left">
          <ArchiveSelector
            v-for="n in nsFilesKeys"
            :id="n"
            :key="n"
            :initial-value="nsFiles[n]"
            :disabled="taskInProgress"
            class="my-1"
            removable
            @repo-change="handleRepoChange"
            @repo-remove="handleRepoRemove"
          />
          <a
            :class="{ 'disabled': taskInProgress }"
            href="#"
            class="mt-1 me-auto"
            type="button"
            style="text-decoration: none"
            @click="handleRepoAdd"
          >
            + Add Namespaces
          </a>
        </div>
        <div class="d-flex mt-4">
          <select
            v-model="selectedLang"
            :disabled="taskInProgress"
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
            v-model="selectedEndian"
            :disabled="taskInProgress"
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
              :id="flag.flag"
              v-model="flag.value"
              :disabled="taskInProgress"
              class="form-check-input"
              type="checkbox"
            />
            <label class="form-check-label" :for="flag.flag">
              {{ flag.name }}
              <code>{{ flag.flag }}</code>
            </label>
            <p v-if="flag.description" class="small">
              {{ flag.description }}
            </p>
          </div>
          <p v-if="command" class="mt-2 mb-0">Generation command:</p>
          <pre v-if="command" style="white-space: pre-wrap">{{ command }}</pre>
          <div class="d-flex align-items-center mt-4 flex-wrap">
            <button
              v-if="taskInProgress"
              type="button"
              class="btn btn-secondary me-3 mb-4"
              @click="handleCancel"
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
              v-if="loadingStatus !== ''"
              class="d-flex flex-nowrap align-items-center mb-4"
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
                <p v-if="loadingStatus === 'SUCCESS'" class="small mb-0">
                  Download here: <a :href="resultURL">{{ resultURL }}</a>
                </p>
                <p v-else-if="loadingStatus === 'FAILURE'" class="small mb-0">
                  {{ loadingMessage }}
                </p>
                <p v-else-if="loadingStatus === 'CANCELED'" class="small mb-0">
                  Generation was canceled. You can submit another.
                  <a href="#" @click="loadingStatus = ''">Hide</a>
                </p>
                <p v-else class="small mb-0">
                  This process can take up to several minutes. Leave the page open!
                </p>
              </div>
            </div>
          </div>
        </div>
        <Description />
      </form>
    </div>
    <footer class="container-fluid footer">
      <div class="container d-flex justify-content-center text-center px-5">
        <p class="text-muted mx-3 mb-0">(C) 2021 UAVCAN</p>
        <a class="text-muted mx-3 mb-0" href="https://github.com/UAVCAN/nunaweb">Source</a>
        <a class="text-muted mx-3 mb-0" href="https://nunavut.readthedocs.io/en/latest/README.html">Nunavut Docs</a>
        <a class="text-muted mx-3 mb-0" href="https://uavcan.org">UAVCAN</a>
      </div>
    </footer>
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
      this.currentNSFilesLen++;
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

        if (data.command !== '') {
          this.command = data.command;
        }

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

.footer {
  padding: 1rem;
  background-color: #EEE;
}

.text-muted {
  color: #AAA;
  text-decoration: none;
}

a.text-muted:hover {
  text-decoration: underline;
}

.noline {
  text-decoration: none;
}
</style>
