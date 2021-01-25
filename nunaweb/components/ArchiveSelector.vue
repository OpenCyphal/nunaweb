<template>
  <div class="d-flex align-items-center">
    <input
      type="text"
      class="form-control mt-2"
      placeholder="Github link to namespace repository"
      name="archive_url"
      v-model="namespaceRepo"
      v-on:change="handleURLChange"
      :disabled="isFile || disabled"
      />
    <p class="px-2 mt-2 mb-0">or</p>
    <label
      class="btn btn-primary text-nowrap mt-2"
      v-bind:class="{ disabled: disabled }"
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
      v-bind:class="{ disabled: disabled }"
      type="button"
      class="btn btn-secondary text-nowrap mt-2"
    >
      Clear
    </button>
    <button
      v-if="removable"
      type="button"
      v-bind:class="{ disabled: disabled }"
      v-on:click="$emit('repo-remove', id)"
      class="btn btn-danger text-nowrap mt-2 ms-2"
    >
      Remove
    </button>
  </div>
</template>

<style>
</style>

<script>
export default {
  data() {
    return {
      namespaceRepo: this.initialValue || '',
      isFile: false
    };
  },
  props: {
    disabled: Boolean,
    removable: Boolean,
    id: String,
    initialValue: String
  },
  methods: {
    handleFileSelect(e) {
      this.isFile = true;
      this.namespaceRepo = e.target.files[0].name;
      this.$emit('repo-change', this.id, e.target.files[0]);
    },

    handleURLChange(e) {
      console.log(e);
      this.namespaceRepo = e.target.value;
      this.$emit('repo-change', this.id, e.target.value);
    },

    clearFile(e) {
      console.log('clear');
      this.isFile = false;
      this.namespaceRepo = '';
      this.$emit('repo-change', this.id, null);
    }
  }
}
</script>
