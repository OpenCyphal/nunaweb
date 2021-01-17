<template>
  <div class="d-flex mt-3 align-items-center mb-3">
    <input
      type="text"
      class="form-control mt-2"
      placeholder="Github link to namespace repository"
      name="archive_url"
      v-model="namespaceRepo"
      v-on:change="$emit('ns-namechange', $event.target.value)"
      :disabled="isFile"
      />
    <p class="px-2 mt-2 mb-0">or</p>
    <label
      class="btn btn-primary text-nowrap mt-2"
      v-if="!isFile"
    >
      Upload .zip
      <input
        ref="fileInput"
        type="file"
        name="archive"
        accept="application/zip"
        hidden
        v-on:change="handleFileSelect"
        />
    </label>
    <button
      v-else
      v-on:click="clearFile"
      type="button"
      class="btn btn-secondary text-nowrap mt-2"
    >
      Clear
    </button>
  </div>
</template>

<style>
</style>

<script>
export default {
  data() {
    return {
      namespaceRepo: '',
      isFile: false
    };
  },
  methods: {
    handleFileSelect(e) {
      this.isFile = true;
      this.namespaceRepo = e.target.files[0].name;
      this.$emit('file-change', e.target.files[0]);
    },
    clearFile(e) {
      console.log('clear');
      this.isFile = false;
      this.namespaceRepo = '';
      this.$emit('file-change', null);
    }
  }
}
</script>
