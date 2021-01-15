<!-- TODO: Break this thing up! It's massive. -->
<template>
  <div class="container d-flex flex-column align-items-center text-center p-5">
    <form style="max-width: 960px">
      <Logo style="margin-bottom: 3rem" />
      <h1 class="title">
        nunaweb
      </h1>
      <h2 class="lead">
        generate DSDL code from the web
      </h2>
      <div class="d-flex mt-3 align-items-center mb-3">
        <input
          type="text"
          class="form-control mt-2"
          placeholder="Github link to namespace repository"
          v-model="namespaceRepo"
          :disabled="isFile"
        />
        <p class="px-2 mt-2 mb-0">or</p>
        <label
          class="btn btn-primary text-nowrap mt-2"
          v-if="!isFile"
        >
          Upload .zip
          <input
            type="file"
            accept="application/zip"
            hidden
            v-on:change="handleFileUpload"
          />
        </label>
        <button v-else class="btn btn-secondary text-nowrap mt-2">
          Clear
        </button>
      </div>
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
        <input type="submit" class="btn btn-primary mt-4" value="Submit" />
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
      namespaceRepo: '',
      isFile: false,
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
    handleFileUpload(event) {
      console.log(event);
      this.isFile = true;
      this.namespaceRepo = event.target.files[0].name;
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
