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
      />
      <div class="d-flex">
        <select v-model="selectedLang" class="form-select me-2" aria-label="Target Language">
          <option
            v-for="lang in languages"
            :key="lang.value"
            :disabled="lang.disabled"
            :value="lang.value"
          >
          {{ lang.name }}
          </option>
        </select>
        <select v-model="selectedEndian" class="form-select" aria-label="Select Endianness">
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
          <input
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
              v-else-if="loadingStatus === 'FAILURE'"
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
      fetch('http://localhost:5000/upload', {
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
          this.loadingTimeout = setInterval(this.handleProcessing, 500);
        })
        .catch(err => console.log(err));
    },
    handleProcessing() {
      fetch('http://localhost:5000' + this.loadingURL)
        .then(res => res.json())
        .then((data) => {
          this.loadingStatus = data.state;
          this.loadingMessage = data.status;
          if (data.state === 'SUCCESS') {
            this.resultURL = data.result;
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
