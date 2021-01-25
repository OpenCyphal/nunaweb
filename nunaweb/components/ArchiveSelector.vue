<template>
  <div class="d-flex align-items-center">
    <input
      v-model="namespaceRepo"
      :disabled="isFile || disabled"
      type="text"
      class="form-control mt-2"
      placeholder="Github link to namespace repository"
      name="archive_url"
      @change="handleURLChange"
    />
    <p class="px-2 mt-2 mb-0">or</p>
    <label
      v-if="!isFile"
      class="btn btn-primary text-nowrap mt-2"
      :class="{ disabled: disabled }"
    >
      Upload .zip
      <input
        ref="fileInput"
        type="file"
        name="archive"
        accept="application/zip"
        hidden
        @change="handleFileSelect"
      />
    </label>
    <button
      v-else
      :class="{ disabled: disabled }"
      type="button"
      class="btn btn-secondary text-nowrap mt-2"
      @click="clearFile"
    >
      Clear
    </button>
    <button
      v-if="removable"
      type="button"
      :class="{ disabled: disabled }"
      class="btn btn-danger text-nowrap mt-2 ms-2"
      @click="$emit('repo-remove', id)"
    >
      Remove
    </button>
  </div>
</template>

<style>
</style>

<script>
export default {
  props: {
    disabled: Boolean,
    removable: Boolean,
    id: {
      type: String,
      required: true
    },
    initialValue: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      namespaceRepo: this.initialValue || '',
      isFile: false
    };
  },
  methods: {
    handleFileSelect(e) {
      this.isFile = true;
      this.namespaceRepo = e.target.files[0].name;
      this.$emit('repo-change', this.id, e.target.files[0]);
    },

    handleURLChange(e) {
      this.namespaceRepo = e.target.value;
      this.$emit('repo-change', this.id, e.target.value);
    },

    clearFile(e) {
      this.isFile = false;
      this.namespaceRepo = '';
      this.$emit('repo-change', this.id, null);
    }
  }
}
</script>
