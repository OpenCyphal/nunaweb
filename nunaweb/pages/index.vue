<!-- TODO: Break this thing up! It's massive. -->
<template>
  <div class="container d-flex flex-column align-items-center text-center p-5">
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
        :disabled="['PROGRESS', 'PENDING', 'STARTED', 'RETRY'].includes(loadingStatus)"
        v-on:repo-change="handleRepoChange"
        class="mt-3 mb-3"
      />
      <div class="d-flex">
        <select
          :disabled="['PROGRESS', 'PENDING', 'STARTED', 'RETRY'].includes(loadingStatus)"
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
          :disabled="['PROGRESS', 'PENDING', 'STARTED', 'RETRY'].includes(loadingStatus)"
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
            :disabled="['PROGRESS', 'PENDING', 'STARTED', 'RETRY'].includes(loadingStatus)"
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
        <!--pre>{{ command }}</pre -->
        <a href="#" v-on:click="additionalReposOpen = !additionalReposOpen">
          {{ additionalReposOpen ? "-" : "+" }} Additional namespace repositories
        </a>
        <b-collapse v-model="additionalReposOpen" class="mb-5">
          <ArchiveSelector
            v-for="n in nsFilesKeys"
            :key="n"
            :id="n"
            :initialValue="nsFiles[n]"
            v-on:repo-change="handleRepoChange"
            v-on:repo-remove="handleRepoRemove"
            class="my-1"
            removable
          />
          <button class="btn btn-primary mt-2" type="button" v-on:click="handleRepoAdd">
            Add Repo
          </button>
        </b-collapse>
        <div class="d-flex align-items-center mt-4 flex-wrap">
          <button
            v-if="['PROGRESS', 'PENDING', 'STARTED', 'RETRY'].includes(loadingStatus)"
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

export default {
  data() {
    return {
      loadingStatus: '',
      loadingMessage: '',
      loadingURL: '',
      resultURL: '',
      additionalReposOpen: false,
      loadingTimeout: null,
      nsFiles: {
        '0': null,
        '1': 'https://github.com/UAVCAN/public_regulated_data_types',
        '2': null
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
    // TODO: At the moment, I couldn't figure out a good performant way to
    // get enough information on the namespaces within the repo/archive to
    // display exactly what command to run
    // So for now we'll keep that part backend-only and we can potentially figure
    // it out later.
    command() {
      const flags = this.flags.filter(flag => flag.value).map(flag => flag.flag);
      let command = `nnvg --target-language ${this.selectedLang} `;
      command += this.selectedEndian !== 'any'
        ? `--target-endianness=${this.selectedEndian} ` : '';
      command += flags.join(' ');
      return command;
    },
    nsFilesKeys() {
      return Object.keys(this.nsFiles).filter(key => key !== '0');
    }
  },
  mounted() {
    console.log(this.$route.path)
    if (this.$route.path !== '/') {
      console.log(this.$route.path)
      this.loadingURL = this.$route.path;
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

      this.loading = true;
      this.loadingMessage = 'Uploading...';

      try {
        const data = await api.upload(formData);
        console.log(data);

        this.loadingURL = data.task_url;
        // We push to a status/:statusID route, which
        // enables saving the output in the user's history
        // This allows the user to come back to the status page
        // if they accidentally leave
        // The status page triggers the progress querying
        this.$router.push({ path: this.loadingURL });
      } catch (e) {
        // Error handling
        console.log(e);
      }
    },
    async handleProcessing() {
      try {
        const data = await api.getStatus(this.$route.params.statusID);
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
        console.log(e);
      }
    },
    async handleCancel() {
      try {
        await api.cancel(this.$route.params.statusID);
        this.loadingStatus = 'CANCELED';
        this.loadingMessage = 'Task was canceled.';
        this.loadingURL = '';
        this.resultURL = '';
        clearInterval(this.loadingTimeout);
      } catch (e) {
        console.log(e);
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
</style>
