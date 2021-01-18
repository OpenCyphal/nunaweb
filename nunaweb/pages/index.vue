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
        v-on:ns-namechange="handleRepoURLChange"
        v-on:file-change="handleFileSelect"
        :disabled="['PROGRESS', 'PENDING', 'STARTED', 'RETRY'].includes(loadingStatus)"
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
          class="form-select me-2"
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
              <label>{{ loadingMessage }}</label>
              <p class="small mb-0" v-if="loadingStatus === 'SUCCESS'">
              Download here: <a :href="resultURL">{{ resultURL }}</a>
              </p>
              <p class="small mb-0" v-else-if="loadingStatus === 'FAILURE'">
              Generation failed.
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
export default {
  data() {
    const endians = [
      {
        name: 'Little Endian',
        value: 'little'
      },
      {
        name: 'Any Endian',
        value: 'any'
      },
      {
        name: 'Big Endian',
        value: 'big'
      }
    ];

    const languages = [
      {
        name: 'C',
        value: 'c'
      },
      {
        name: 'C++ (coming soon)',
        value: 'c++',
        disabled: true
      },
      {
        name: 'Python (coming soon)',
        value: 'python',
        disabled: true
      }
    ];

    const flags = [
      {
        name: 'Enable serialization asserts',
        description: 'Instruct support header generators to generate language-specific assert statements as part of serialization routines. By default the serialization logic generated may make assumptions based on documented requirements for calling logic that could expose a system to undefined behaviour. The alternative, for langauges that do not support exception handling, is to use assertions designed to halt a program rather than execute undefined logic.',
        flag: '--enable-serialization-asserts',
        value: true
      },
      {
        name: 'Omit float serialization support',
        flag: '--omit-float-serialization-support',
        description: 'Instruct support header generators to omit support for floating point operations in serialization routines. This will result in errors if floating point types are used, however; if you are working on a platform without IEEE754 support and do not use floating point types in your message definitions this option will avoid dead code or compiler errors in generated serialization logic.',
        value: false
      }
    ]

    return {
      loadingStatus: '',
      loadingMessage: '',
      loadingURL: '',
      resultURL: '',
      loadingTimeout: null,
      nsRepo: '',
      nsFile: null,
      selectedLang: 'c',
      selectedEndian: 'little',
      endians,
      flags,
      languages
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
    handleFileSelect(file) {
      // TODO: Perhaps handle this cleaner
      this.nsFile = file;
    },
    handleRepoURLChange(url) {
      this.nsRepo = url;
    },
    handleSubmit(event) {
      event.preventDefault();
      event.stopPropagation();

      // Append data
      const formData = new FormData();
      if (this.nsFile) {
        console.log(this.nsFile);
        formData.append('archive', this.nsFile);
      } else {
        formData.append('archive_url', this.nsRepo + '/archive/master.zip');
      }
      formData.append('target_lang', this.selectedLang);
      formData.append('target_endian', this.selectedEndian);
      formData.append('flags', this.flags.filter(flag => flag.value).map(flag => flag.flag));

      this.loading = true;
      this.loadingMessage = 'Uploading...';

      console.log(formData);
      fetch(process.env.apiURL + '/upload', {
        method: 'POST',
        body: formData
      })
        .then((res) => {
          if (!res.ok) {
            console.log('Fetch error');
          }
          return res.json();
        })
        .then((data) => {
          this.loadingURL = data.task_url;
          // We push to a status/:statusID route, which
          // enables saving the output in the user's history
          // This allows the user to come back to the status page
          // if they accidentally leave
          // The status page triggers the progress querying
          this.$router.push({ path: this.loadingURL });
        })
        .catch(err => console.log(err));
    },
    handleProcessing() {
      fetch(process.env.apiURL + this.loadingURL)
        .then(res => res.json())
        .then((data) => {
          this.loadingStatus = data.state;
          this.loadingMessage = data.status;
          if (data.state === 'SUCCESS') {
            this.resultURL = data.result;
            clearInterval(this.loadingTimeout);
          } else if (data.state === 'CANCELED') {
            clearInterval(this.loadingTimeout);
          }
        })
        .catch(err => console.log(err));
    },
    handleCancel() {
      fetch(process.env.apiURL + this.loadingURL + '/cancel')
        .then((res) => {
          if (!res.ok) {
            this.loadingStatus = 'CANCELED';
            this.loadingMessage = '';
            this.loadingURL = '';
            this.resultURL = '';
            clearInterval(this.loadingTimeout);
          }
        })
        .catch(err => console.log(err));
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
